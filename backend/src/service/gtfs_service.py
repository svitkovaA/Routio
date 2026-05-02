"""
file: gtfs_service.py

This file implements an asynchronous GTFS data service used by the routing
engine. It is responsible for downloading, extracting and processing static
GTFS dataset.
"""

import asyncio
from dataclasses import dataclass
import shutil
from typing import DefaultDict, Dict, List, Set, Tuple, cast
import zipfile
import numpy as np
import pandas as pd
from datetime import date, datetime
from collections import defaultdict
import requests
import unicodedata
import re
from collections import Counter
from shared.geo_math import GeoMath
from service.district_service import DistrictService
from config.datasets import GTFS_DATASETS, GTFS_DIR, GTFS_DATASET
from models.route import TZ, Departure, OtherDeparture, OtherOptions
from service.service_base import ServiceBase
from sklearn.neighbors import BallTree      # type: ignore[import-untyped]

@dataclass(frozen=True)
class StopRecord:
    """
    Represents a single processed stop used for search and suggestions.
    """
    # Display name of the stop
    name: str

    # Stop coordinates
    lat: float
    lon: float
    
    # Flags indicating transport presence
    is_train: bool
    is_bus: bool

@dataclass(frozen=True)
class _Dataset:
    """
    Processed GTFS data representation.
    """
    calendar: pd.DataFrame
    calendar_dates: pd.DataFrame

    # Maps route_short_name to route_id
    route_short_name_to_id: Dict[str, str]

    # Maps trip_id to { route_id, service_id and trip headsign } 
    trip_id_to_info: Dict[str, Dict[str, str]]

    # Maps stop_id to list of (trip_id, departure_time)
    stop_id_to_departures: DefaultDict[str, List[Tuple[str, str]]]

    # Maps trip_id to ordered list of (stop_id, departure_time, stop_sequence)
    trip_id_to_stop_sequence: Dict[str, List[Tuple[str, str, int]]]

    # Maps trip_id to { stop_id: departure_time }
    trip_id_to_stop_times: Dict[str, Dict[str, str]]

    # Maps stop_id to geographic coordinated (lat, lon)
    stop_id_to_coords: Dict[str, Tuple[float, float]]

    # Spatial BallTree index for public transport stops
    stops_tree: BallTree

@dataclass(frozen=True)
class _GTFSState:
    # Maps dataset name to dataset
    datasets: Dict[str, _Dataset]

    # Maps agency name to dataset name
    agency_name_to_dataset_name: Dict[str, str]
    
    # List of all stops across all datasets
    all_stops: List[StopRecord]

class GTFSService(ServiceBase[_GTFSState]):
    """
    Service responsible for downloading, parsing and processing GTFS data
    """

    # Earth radius in meters
    EARTH_RADIUS_M = 6371000
    
    # Maximum clustering distance between stops
    MAX_DISTANCE_M = 200
    
    def __init__(self) -> None:
        super().__init__()
        # Ensures safe concurrent reload access
        self.__lock = asyncio.Lock()

        # Maps dataset name to reference_date to set(service_id)
        self.__services_cache: Dict[str, Dict[date, Set[str]]] = {}
        
        # District service instance
        self.__district_service = DistrictService.get_instance()

    def get_trip_stops(
        self,
        dataset_name: str,
        trip_id: str
    ) -> List[Tuple[str, str, int]] | None:
        """
        Returns the ordered stop sequence for a given trip.

        Args:
            dataset_name: GTFS dataset name
            trip_id: GTFS trip identifier

        Returns:
            List of Tuples (stop_id, departure_time, stop_sequence)
        """
        state = self._get_state()
        if dataset_name not in state.datasets:
            return None

        # Returns ordered stop sequence for a trip
        return state.datasets[dataset_name].trip_id_to_stop_sequence.get(trip_id)
    
    def get_stop_coordinates(
        self,
        dataset_name: str,
        stop_id: str
    ) -> Tuple[float, float] | None:
        """
        Returns geographic coordinates for a given stop.

        Args:
            dataset_name: GTFS dataset name
            stop_id: GTFS stop identifier

        Returns:
            Tuple (latitude, longitude)
        """
        state = self._get_state()
        if dataset_name not in state.datasets:
            return None

        # Returns geographic coordinates for a stop
        return state.datasets[dataset_name].stop_id_to_coords.get(stop_id)

    def get_departures_via(
        self,
        agency_name: str,
        from_stop_id: str,
        to_stop_id: str, 
        route_short_name: str, 
        aimed_start_time: datetime, 
        n_prev: int = 4, 
        n_next: int = 20
    ) -> OtherOptions:
        """
        Returns nearby departures for the given route between two stops.
        
        Args:
            agency_name: GTFS agency name
            from_stop_id: Origin stop identifier
            to_stop_id: Destination stop identifier
            route_short_name: The public route code (route_short_name)
            aimed_start_time: Reference time in ISO format
            n_prev: Number of departures considered before the reference time
            n_next: Number of departures considered after the reference time
        
        Returns:
            OtherOptions object containing ordered list of departures and index
            of the currently selected departure
        """
        dataset = self.__get_dataset_by_agency(agency_name)
        dataset_name = self.get_dataset_name_by_agency(agency_name)
        if dataset is None or dataset_name is None:
            return OtherOptions()

        # Parse and normalize time to local timezone
        ref_dt_local = (
            aimed_start_time.astimezone(TZ) 
            if aimed_start_time.tzinfo
            else aimed_start_time.replace(tzinfo=TZ)
        )

        # Extract reference date, previous date and next date
        reference_date = aimed_start_time.date()
        previous_date = reference_date - pd.Timedelta(days=1)
        next_date = reference_date + pd.Timedelta(days=1)

        # Get route_id from route_short_name
        route_id = dataset.route_short_name_to_id.get(route_short_name)
        if not route_id:
            return OtherOptions()
        
        # Determine active services
        valid_services_previous = self.__valid_services_for_date(dataset_name, dataset, previous_date)
        valid_services_today = self.__valid_services_for_date(dataset_name, dataset, reference_date)
        valid_services_next = self.__valid_services_for_date(dataset_name, dataset, next_date)

        # Identify trips that contain the destination stop
        trips_with_dest = {tid for tid, _ in dataset.stop_id_to_departures.get(to_stop_id, [])}

        # Aggregate departures for previous, current and next day
        all_departures: List[OtherDeparture] = []
        for date, services in [
            (previous_date, valid_services_previous), 
            (reference_date, valid_services_today), 
            (next_date, valid_services_next)
        ]:
            # Collect departures for given date and valid services
            departures = self.__collect_departures_for_date(
                dataset,
                from_stop_id,
                route_id,
                trips_with_dest,
                services
            )

            # Converts GTFS time HH:MM:SS to YYYY-MM-DDTHH:MM:SS time_zone
            for departure in departures:
                td = pd.to_timedelta(departure.departure_time_str)                           # type: ignore[type-arg]
                dt = datetime.combine(date, datetime.min.time(), tzinfo=TZ) + td
                departure.departure_time = dt
            
            # Append to global list
            all_departures.extend(departures)

        # Sort departures by datetime
        all_departures.sort(key=lambda x: x.departure_time)

        # Find the first departure at or after reference time
        index = next((
            i 
            for i, dep in enumerate(all_departures) 
            if dep.departure_time >= ref_dt_local
        ), 0)

        # Maximum allowed time gap between results
        MAX_DEPARTURE_GAP = pd.Timedelta(hours=2)

        # Collect previous departures
        previous: List[OtherDeparture] = []
        for i in list(reversed(range(index))):
            current = all_departures[i]

            # Insert first
            if not previous:
                gap = all_departures[index].departure_time - current.departure_time

                if gap > MAX_DEPARTURE_GAP:
                    break

                previous.append(current)
                continue
            gap = previous[-1].departure_time - current.departure_time

            # Time gap is bigger than maximal allowed, rest is truncated
            if gap > MAX_DEPARTURE_GAP:
                break

            previous.append(current)

            # Stop when enough previous results collected
            if len(previous) >= n_prev:
                break
        
        # Restore order
        previous.reverse()

        # Collect future departures
        nexts: List[OtherDeparture] = []
        for i in range(index, len(all_departures)):
            current = all_departures[i]

            # Insert first
            if not nexts:
                nexts.append(current)
                continue
            gap = current.departure_time - nexts[-1].departure_time

            # Time gap is bigger than maximal allowed, rest is truncated
            if gap > MAX_DEPARTURE_GAP:
                break
            nexts.append(current)

            # Stop when enough next results collected
            if len(nexts) >= n_next:
                break

        # Merge previous and next departures
        final_departures = previous + nexts

        # Determine index of selected departure
        current_index = len(previous) if nexts else len(previous) - 1

        # Return departures
        return OtherOptions(
            departures=[
                Departure(
                    departureTime=dep.departure_time,
                    direction=dep.direction,
                    tripId=dep.trip_id
                )
                for dep in final_departures
            ],
            currentIndex=current_index
        )
        
    def get_stops_tree(self, agency_name: str) -> BallTree:
        """
        Returns the BallTree used for spatial stop queries.

        Args:
            agency_name: GTFS agency name

        Returns:
            BallTree structure containing stop coordinates
        """
        dataset = self.__get_dataset_by_agency(agency_name)
        if dataset is None:
            raise ValueError(f"Agency name: {agency_name} not found in GTFSService cache")

        return dataset.stops_tree

    def get_dataset_name_by_agency(self, agency_name: str) -> str | None:
        """
        Converts agency name to dataset name.

        Args:
            agency_name: GTFS agency name

        Returns:
            Dataset name
        """
        state = self._get_state()
        return state.agency_name_to_dataset_name.get(agency_name)

    def search_stops(self, query: str, limit: int = 5) -> List[StopRecord]:
        """
        Performs prefix-based search over all stops.

        Args:
            query: Input string
            limit: Maximum number of results returned

        Returns:
            List of matching StopRecords ordered by relevance
        """
        state = self._get_state()

        # Normalize and tokenize query
        q_tokens = self.normalize_query(query).split()
        if not q_tokens:
            return []

        scored: List[Tuple[int, StopRecord]] = []

        # Iterate through all stops
        for stop in state.all_stops:
            name_norm = self.normalize_query(stop.name)
            tokens = name_norm.split()

            # Every query token must match at least one stop token
            if not all(
                any(t.startswith(qt) for t in tokens)
                for qt in q_tokens
            ):
                continue

            # Exact match
            if name_norm == " ".join(q_tokens):
                score = -1
            # Match at beginning
            elif tokens and tokens[0].startswith(q_tokens[0]):
                score = 0 
            # Match somewhere else
            elif any(t.startswith(q_tokens[0]) for t in tokens):
                score = 1
            else:
                score = 2
            scored.append((score, stop))

        # Sort by score and name
        scored.sort(key=lambda x: (x[0], x[1].name))
        return [s for _, s in scored[:limit]]

    async def reload(self) -> None:
        """
        Reload the GTFS dataset.
        """
        print("Loading GTFS cache")
        
        results = await asyncio.gather(*[
            asyncio.to_thread(self.__load_new_state, dataset)
            for dataset in GTFS_DATASETS
        ])

        datasets: Dict[str, _Dataset] = {}
        agency_name_to_dataset_name: Dict[str, str] = {}
        all_stops: List[StopRecord] = []

        # Prepare state dicts
        for (dataset_obj, agency_map, processed_stops), dataset_cfg in zip(results, GTFS_DATASETS):
            dataset_name = dataset_cfg["name"]
            datasets[dataset_name] = dataset_obj

            # Join agency maps
            for agency_name, ds_name in agency_map.items():

                # Duplicities found
                if agency_name in agency_name_to_dataset_name:
                    print(f"WARNING: duplicate agency_name '{agency_name}'")

                agency_name_to_dataset_name[agency_name] = ds_name
                
                # Collect processed stops
                for name, lat, lon, is_train, is_bus in processed_stops:
                    all_stops.append(StopRecord(name, lat, lon, is_train, is_bus))
              
        # Deduplicate collected stops
        unique: Dict[Tuple[str, float, float], StopRecord] = {}
        for stop in all_stops:
            key = (stop.name, round(stop.lat, 5), round(stop.lon, 5))

            if key not in unique:
                unique[key] = stop

        new_state = _GTFSState(
            datasets=datasets,
            agency_name_to_dataset_name=agency_name_to_dataset_name,
            all_stops=list(unique.values())
        )

        # Ensure atomic state swap
        async with self.__lock:
            self._set_state(new_state)
            self.__services_cache.clear()
    
    @staticmethod
    def normalize_query(s: str) -> str:
        """
        Normalizes string for search.

        Args:
            s: query string

        Returns:
            normalize string
        """
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
        
        # Replace non-alphanumeric with space
        s = re.sub(r"[^a-z0-9]+", " ", s)

        # Remove extra spaces
        s = re.sub(r"\s+", " ", s).strip()
        
        return s

    def __valid_services_for_date(
        self,
        dataset_name: str,
        dataset: _Dataset,
        ref_date: date
    ) -> Set[str]:
        """
        Determine all GTFS service ids valid for a given date.
        
        Args:
            dataset_name: GTFS dataset name
            dataset: Current GTFS dataset
            ref_date: Reference date for which valid services are requested

        Returns:
            Set of service_id values active on the given day
        """
        # Return cached result if available
        cache = self.__services_cache.setdefault(dataset_name, {})
        cached = cache.get(ref_date)
        if cached is not None:
            return cached

        # Map date to day of the week
        weekday = ref_date.strftime("%A").lower()

        # Convert date to YYYYMMDD integer
        ymd = int(ref_date.strftime("%Y%m%d"))

        # Filter services active on given weekday and date range
        services = dataset.calendar[
            (dataset.calendar[weekday] == 1) &
            (dataset.calendar["start_date"] <= ymd) &
            (dataset.calendar["end_date"] >= ymd)
        ]["service_id"].tolist()

        # Remove duplicities
        services_set = set(services)

        # Process service exceptions for given date
        exceptions = dataset.calendar_dates[dataset.calendar_dates["date"] == ymd]
        added = exceptions[exceptions["exception_type"] == 1]["service_id"].tolist()
        removed = exceptions[exceptions["exception_type"] == 2]["service_id"].tolist()

        # Add extra services
        services_set.update(added)

        # Remove cancelled services
        services_set.difference_update(removed)

        # Store the result in cache
        self.__services_cache[dataset_name][ref_date] = services_set
        return services_set

    def __get_dataset_by_agency(self, agency_name: str) -> _Dataset | None:
        """"
        Retrieve dataset by agency name.

        Args:
            agency_name: GTFS agency name
        
        Returns:
            Dataset for the agency name
        """
        dataset_name = self.get_dataset_name_by_agency(agency_name)
        if dataset_name is None:
            return None
        
        state = self._get_state()
        return state.datasets.get(dataset_name)

    @staticmethod
    def __collect_departures_for_date(
        dataset: _Dataset,
        from_stop_id: str,
        route_id: str,
        trips_with_dest: Set[str],
        valid_services: Set[str]
    ) -> List[OtherDeparture]:
        """
        Collects departures from a given origin stop for a specific route and
        set of valid services.

        Args:
            dataset: Current GTFS dataset
            from_stop_id: Origin stop identifier
            route_id: Internal GTFS route_id
            trips_with_dest: Set of trip_ids that reach destination stop
            valid_services: Active service_ids for the given date

        Returns:
            List of candidate departures without resolved datetime
        """
        departures: List[OtherDeparture] = []

        # Iterate over all trips departing from origin stop
        for trip_id, departure_time in dataset.stop_id_to_departures.get(from_stop_id, []):
            trip_info = dataset.trip_id_to_info.get(trip_id)
            if not trip_info:
                continue

            # Filter by matching route
            if trip_info["route_id"] != route_id:
                continue

            # Filter by active service on given date
            if trip_info["service_id"] not in valid_services:
                continue
            
            # Ensure trip reaches destination stop
            if trip_id not in trips_with_dest:
                continue

            # Create departure
            departures.append(
                OtherDeparture(
                    trip_id=trip_id,
                    departure_time=datetime.min,        # Dummy value
                    direction=trip_info.get("headsign", ""),
                    departure_time_str=departure_time
                )
            )

        return departures
    
    @staticmethod
    def __use_parent_stations(stops: pd.DataFrame) -> bool:
        """
        Determines whether parent stations should be used based on their proportion
        in the dataset.
        
        Args:
            stops: stops.txt DataFrame
            
        Returns:
            True if parent stations are sufficiently present, False otherwise
        """
        if "location_type" not in stops.columns:
            return False

        parent_count = (stops["location_type"] == 1).sum()
        total = len(stops)

        ratio = parent_count / total if total > 0 else 0

        return ratio > 0.1
    
    @staticmethod
    def __filter_unused_stops(
        stops: pd.DataFrame,
        stop_times: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Filters out stops that are not used in any trip.
        
        Args:
            stops: stops.txt DataFrame
            stop_times: stop_times.txt DataFrame
            
        Returns:
            Filtered DataFrame containing only stops that are referenced in trips
        """
        # Collect all stop_ids that are actually used in trips
        used_stop_ids = stop_times["stop_id"].unique()
        
        # Keep only stops that appear in stop_times
        filtered = stops[stops["stop_id"].isin(used_stop_ids)]
        return filtered
    
    @staticmethod
    def __get_stop_modes(
        stops: pd.DataFrame,
        stop_times: pd.DataFrame,
        trips: pd.DataFrame,
        routes: pd.DataFrame,
        aggregate_to_parent: bool
    ) -> Dict[str, Set[int]]:
        """
        Builds mapping from stop to transport modes.

        Args:
            stops: stops.txt
            stop_times: stop_times.txt
            trips: trips.txt
            routes: routes.txt
            aggregate_to_parent: Whether child stops should be aggregated to parent

        Returns:
            Mapping stop_id to set of route types
        """
        merged = stop_times.merge(trips, on="trip_id").merge(routes, on="route_id")

        # Optional mapping child stop to parent station
        parent_map = {}
        if aggregate_to_parent and "parent_station" in stops.columns:
            parent_map = dict(zip(stops["stop_id"], stops["parent_station"]))

        mapping: Dict[str, Set[int]] = {}

        # Group by stop_id and collect all route types
        for stop_id, group in merged.groupby("stop_id"):
            parent = parent_map.get(stop_id)
            
            # Use parent station if available, otherwise original stop_id
            target_id = parent if pd.notna(parent) and parent else stop_id
            target_id = str(target_id)

            mapping.setdefault(target_id, set())
            mapping[target_id].update(group["route_type"].astype(int).unique())

        return mapping
    
    @staticmethod
    def __get_stop_routes(
        stops: pd.DataFrame,
        stop_times: pd.DataFrame,
        trips: pd.DataFrame,
        aggregate_to_parent: bool
    ) -> Dict[str, Set[str]]:
        """
        Builds mapping from stop to route_ids.

        Args:
            stops: stops.txt
            stop_times: stop_times.txt
            trips: trips.txt
            aggregate_to_parent: Whether child stops should be aggregated to parent

        Returns:
            Mapping stop_id to set of route_id
        """

        merged = stop_times.merge(trips, on="trip_id")

        parent_map = {}
        if aggregate_to_parent and "parent_station" in stops.columns:
            parent_map = dict(zip(stops["stop_id"], stops["parent_station"]))

        mapping: Dict[str, Set[str]] = {}

        for stop_id, group in merged.groupby("stop_id"):
            parent = parent_map.get(stop_id)

            target_id = parent if pd.notna(parent) and parent else stop_id
            target_id = str(target_id)

            mapping.setdefault(target_id, set())
            mapping[target_id].update(group["route_id"].astype(str).unique())

        return mapping
    
    @staticmethod
    def __cluster_stops(coords_rad: np.ndarray) -> List[List[int]]:
        """
        Clusters stops based on spatial proximity using radius-based connectivity.

        Args:
            coords_rad: Array of coordinates in radians

        Returns:
            List of clusters, where each cluster is a list of indices into coords_rad
        """
        
        # Spatial index for fast radius queries
        tree = BallTree(coords_rad, metric="haversine")

        visited: Set[int] = set()
        clusters: List[List[int]] = []

        for i in range(len(coords_rad)):
            if i in visited:
                continue

            # Find neighbors within radius
            indices = tree.query_radius(
                coords_rad[i].reshape(1, -1),
                r=GTFSService.MAX_DISTANCE_M / GTFSService.EARTH_RADIUS_M
            )[0]

            cluster: List[int] = []
            stack = list(indices)

            # Ensure transitive clustering
            while stack:
                index = int(stack.pop())
                if index in visited:
                    continue

                visited.add(index)
                cluster.append(index)

                # Expand cluster via neighbors
                neighbors = tree.query_radius(
                    coords_rad[index].reshape(1, -1),
                    r=GTFSService.MAX_DISTANCE_M / GTFSService.EARTH_RADIUS_M
                )[0]

                stack.extend(neighbors)

            clusters.append(cluster)

        return clusters
    
    @staticmethod
    def __get_mode_flags(modes: Set[int]) -> Tuple[bool, bool]:
        """
        Converts GTFS route_type values into simplified transport flags.

        Args:
            modes: Set of GTFS route_type values

        Returns:
            Tuple (is_train, is_bus)
        """
        is_train = any(m in {2, 100, 109} for m in modes)
        is_bus = any(m in {3, 700, 0} for m in modes)
        return is_train, is_bus
    
    @staticmethod
    def __merge_close_clusters(
        cluster_info: List[Tuple[List[int], float, float, Set[int]]],
        stop_ids: List[str],
        stop_routes: Dict[str, Set[str]],
        coords_deg: np.ndarray,
        max_merge_distance_m: int
    ) -> List[Tuple[List[int], float, float, Set[int]]]:
        """
        Merges nearby clusters based on spatial distance and transport similarity.

        Args:
            cluster_info: List of clusters
            stop_ids: Mapping index to stop_id
            stop_routes: Mapping stop_id to set(route_id)
            coords_deg: Coordinates in degrees (lat, lon)
            max_merge_distance_m: Maximum distance between clusters to allow merge

        Returns:
            List of merged clusters with updated centroid and modes
        """
        merged: List[Tuple[List[int], float, float, Set[int]]] = []
        
        # Tracks which clusters were already merged
        used: Set[int] = set()

        # Precompute route sets and mode flags for each cluster
        cluster_routes: List[Set[str]] = []
        cluster_flags: List[Tuple[int, int]] = []
        for c, _, _, modes in cluster_info:
            routes: Set[str] = set()
            
            # Collect all routes passing through cluster
            for index in c:
                routes |= stop_routes.get(stop_ids[index], set())

            cluster_routes.append(routes)
            
            # Convert GTFS route types into simplified flags
            cluster_flags.append(GTFSService.__get_mode_flags(modes))

        # Compare clusters pairwise
        for i, (c1, lat1, lon1, modes1) in enumerate(cluster_info):
            if i in used:
                continue

            current_cluster = list(c1)
            current_modes = set(modes1)

            for j, (c2, lat2, lon2, modes2) in enumerate(cluster_info):
                if i == j or j in used:
                    continue

                # Distance between clusters
                dist = GeoMath.haversine_distance_km(lat1, lon1, lat2, lon2) * 1000

                shared_routes = cluster_routes[i] & cluster_routes[j]
                same_mode = cluster_flags[i] == cluster_flags[j]

                # Clusters are close and share routes or same transport type
                if dist <= max_merge_distance_m and (shared_routes or same_mode):
                    # Merge indices
                    current_cluster.extend(c2)
                    
                    # Merge transport modes
                    current_modes |= modes2
                    used.add(j)

            used.add(i)

            # Recompute center of merged cluster
            coords = coords_deg[current_cluster]

            mean_lat = float(coords[:, 0].mean())
            mean_lon = float(coords[:, 1].mean())

            merged.append((current_cluster, mean_lat, mean_lon, current_modes))

        return merged
    
    def __process_stop_groups(
        self,
        stops: pd.DataFrame,
        stop_modes: Dict[str, Set[int]],
        stop_routes: Dict[str, Set[str]]
    ) -> List[Tuple[str, float, float, bool, bool]]:
        """
        Processes stops grouped by name and produces final unified stop records.
        
        Args:
            stops: DataFrame containing stop_id, stop_name, stop_lat, stop_lon
            stop_modes: Mapping stop_id to set of GTFS route_type values
            stop_routes: Mapping stop_id to set of route_id values

        Returns:
            List of tuples (name, lat, lon, is_train, is_bus)
        """
        result: List[Tuple[str, float, float, bool, bool]] = []

        # Process each stop group with identical name separately
        for stop_name, group in stops.groupby("stop_name"):
            
            # Extract coordinates and ids
            coords_deg = group[["stop_lat", "stop_lon"]].to_numpy()
            stop_ids = group["stop_id"].to_list()

            # Prepare initial clusters 
            cluster_info: List[Tuple[List[int], float, float, Set[int]]] = []
            for i in range(len(group)):
                lat, lon = coords_deg[i]
                modes = stop_modes.get(stop_ids[i], set())

                cluster_info.append(([i], lat, lon, modes))

            # Merge clusters based on distance and transport similarity
            merged_clusters = self.__merge_close_clusters(
                cluster_info,
                stop_ids,
                stop_routes,
                coords_deg,
                max_merge_distance_m=1000
            )

            # Determine if multiple clusters share same transport type
            flag_counts = Counter(
                self.__get_mode_flags(modes)
                for _, _, _, modes in merged_clusters
            )
            has_duplicate_flags = any(count > 1 for count in flag_counts.values())
            
            for (_, lat, lon, modes) in merged_clusters:
                is_train, is_bus = self.__get_mode_flags(modes)

                name = str(stop_name)
                district = None

                # Distinguish by district name
                if has_duplicate_flags:
                    district = self.__district_service.get_district(lat, lon)

                    if district:
                        name = f"{name}, {district}"

                result.append((name, lat, lon, is_train, is_bus))

        return result
    
    def __build_parent_stops(
        self,
        stops: pd.DataFrame,
        stop_times: pd.DataFrame,
        trips: pd.DataFrame,
        routes: pd.DataFrame
    ) -> List[Tuple[str, float, float, bool, bool]]:
        """
        Builds unified stop representation using GTFS parent stations.

        Args:
            stops: stops.txt DataFrame
            stop_times: stop_times.txt DataFrame
            trips: trips.txt DataFrame
            routes: routes.txt DataFrame

        Returns:
            List of processed stops (name, lat, lon, is_train, is_bus)
        """
        if "location_type" not in stops.columns:
            return []

        # Select only parent stations and keep only relevant columns
        parents = stops.loc[
            stops["location_type"] == 1,
            ["stop_id", "stop_name", "stop_lat", "stop_lon"]
        ].copy()

        # Aggregate transport modes to parent stations
        stop_modes = self.__get_stop_modes(
            stops,
            stop_times,
            trips,
            routes,
            aggregate_to_parent=True
        )
        
        # Aggregate route_ids to parent stations
        stop_routes = self.__get_stop_routes(
            stops,
            stop_times,
            trips,
            aggregate_to_parent=True
        )

        return self.__process_stop_groups(parents, stop_modes, stop_routes)
    
    def __build_unique_stops(
        self,
        stops: pd.DataFrame,
        stop_times: pd.DataFrame,
        trips: pd.DataFrame,
        routes: pd.DataFrame
    ) -> List[Tuple[str, float, float, bool, bool]]:
        """
        Builds unified stop representation for datasets without parent stations.

        Args:
            stops: stops.txt DataFrame
            stop_times: stop_times.txt DataFrame
            trips: trips.txt DataFrame
            routes: routes.txt DataFrame

        Returns:
            List of processed stops (name, lat, lon, is_train, is_bus)
        """
        
        if "location_type" in stops.columns:
            stops = stops[stops["location_type"] != 1]

        # Keep only relevant columns
        stops = stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]].copy()
        
        # Build mapping stop_id to transport modes
        stop_modes = self.__get_stop_modes(
            stops,
            stop_times,
            trips,
            routes,
            aggregate_to_parent=False
        )
        
        # Build mapping stop_id to routes
        stop_routes = self.__get_stop_routes(
            stops,
            stop_times,
            trips,
            aggregate_to_parent=False
        )

        result: List[Tuple[str, float, float, bool, bool]] = []

        # Process each stop name independently
        for stop_name, group in stops.groupby("stop_name"):
            
            # Extract coordinates
            coords_deg = group[["stop_lat", "stop_lon"]].to_numpy()
            coords_rad = np.radians(coords_deg)
            
            # Map row index to stop_id
            stop_ids: List[str] = group["stop_id"].to_list()

            # Groups stops within radius
            clusters = self.__cluster_stops(coords_rad)

            clustered_rows: List[Dict[str, str | float]] = []

            # Aggregate clusters
            for cluster in clusters:
                # Compute centre of cluster
                mean_lat = float(coords_deg[cluster][:, 0].mean())
                mean_lon = float(coords_deg[cluster][:, 1].mean())

                # Aggregate modes and routes from all stops in cluster
                modes_set: Set[int] = set()
                routes_set: Set[str] = set()

                for index in cluster:
                    sid = stop_ids[index]
                    modes_set |= stop_modes.get(sid, set())
                    routes_set |= stop_routes.get(sid, set())

                # Create synthetic cluster ID
                cluster_id: str = f"{stop_name}_{len(clustered_rows)}"

                # Store aggregated info under new cluster_id
                stop_modes[cluster_id] = modes_set
                stop_routes[cluster_id] = routes_set

                # Create new aggregated stop record
                clustered_rows.append({
                    "stop_id": cluster_id,
                    "stop_name": str(stop_name),
                    "stop_lat": mean_lat,
                    "stop_lon": mean_lon
                })

            # Convert clustered results to DataFrame
            clustered_df = pd.DataFrame(clustered_rows)

            result.extend(
                self.__process_stop_groups(clustered_df, stop_modes, stop_routes)
            )

        return result
    
    def __load_new_state(
        self,
        dataset: GTFS_DATASET
    ) -> Tuple[_Dataset, Dict[str, str], List[Tuple[str, float, float, bool, bool]]]:
        """
        Loads and preprocess the GTFS dataset.

        Args:
            dataset: GTFS dataset configuration

        Returns:
            Initialized _GTFSState instance
        """

        path = GTFS_DIR / self.hash_label(dataset["name"])

        # Recreate GTFS directory
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

        # Download GTFS ZIP archive
        zip_path = path / "gtfs.zip"
        response = requests.get(dataset["url"], timeout=60)
        response.raise_for_status()

        # Save downloaded archive to disk
        with open(zip_path, "wb") as f:
            f.write(response.content)

        # Extract GTFS archive
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(path)

        # Remove temporary ZIP file
        zip_path.unlink()

        # Load GTFS CSV files into DataFrames
        agency = pd.read_csv(path / "agency.txt")                                 # type: ignore[type-arg]
        calendar = pd.read_csv(path / "calendar.txt")                             # type: ignore[type-arg]
        calendar_dates = pd.read_csv(path / "calendar_dates.txt")                 # type: ignore[type-arg]
        stop_times: pd.DataFrame = pd.read_csv(path / "stop_times.txt")           # type: ignore[type-arg]
        stops: pd.DataFrame = pd.read_csv(path / "stops.txt")                     # type: ignore[type-arg]
        trips: pd.DataFrame = pd.read_csv(path / "trips.txt")                     # type: ignore[type-arg]
        routes: pd.DataFrame = pd.read_csv(path / "routes.txt")                   # type: ignore[type-arg]

        agency_name_to_dataset_name: Dict[str, str] = {}
        for name in agency["agency_name"].dropna().unique():
            agency_name_to_dataset_name[name] = dataset["name"]

        # Maps route_short_name to route_id
        route_short_name_to_id: Dict[str, str] = dict(
            zip(routes["route_short_name"], routes["route_id"])
        )

        # Maps trip_id to {route_id, service_id, headsign}
        trip_id_to_info: Dict[str, Dict[str, str]] = {
            str(row["trip_id"]): {
                "route_id": row["route_id"],
                "service_id": row["service_id"],
                "headsign": row.get("trip_headsign", "")
            }
            for _, row in trips.iterrows()
        }

        # Maps stop_id to list of (trip_id, departure_time)
        stop_id_to_departures: DefaultDict[str, List[Tuple[str, str]]] = defaultdict(list)
        for _, row in stop_times.iterrows():
            stop_id_to_departures[row["stop_id"]].append((
                str(row["trip_id"]),
                row["departure_time"]
            ))

        # Maps stop_id to (latitude, longitude)
        stop_id_to_coords: Dict[str, Tuple[float, float]] = dict(
            zip(
                stops["stop_id"],
                zip(stops["stop_lat"], stops["stop_lon"])
            )
        )

        # Sort stop_times for ordered trip sequences
        stop_times_sorted = stop_times.sort_values(["trip_id", "stop_sequence"])

        trip_id_to_stop_sequence: Dict[str, List[Tuple[str, str, int]]] = {}
        trip_id_to_stop_times: Dict[str, Dict[str, str]] = {}

        # Group stop_times by trip_id
        for trip_id, group in stop_times_sorted.groupby("trip_id"):
            trip_id_str = str(cast(str, trip_id))

            # Build ordered stop sequence list
            sequence_list = [
                (row["stop_id"], row["departure_time"], int(row["stop_sequence"]))
                for _, row in group.iterrows()
            ]

            trip_id_to_stop_sequence[trip_id_str] = sequence_list

            # Maps stop_id to departure_time
            trip_id_to_stop_times[trip_id_str] = {
                row["stop_id"]: row["departure_time"]
                for _, row in group.iterrows()
            }

        # Extract stop coordinates
        coordinates = stops[["stop_lat", "stop_lon"]].to_numpy()

        # Convert coordinates to radians
        coordinates_rad = np.radians(coordinates)

        # Build BallTree spatial index
        tree = BallTree(coordinates_rad, metric="haversine")
        
        # Decide processing strategy based on GTFS structure
        if self.__use_parent_stations(stops):
            processed_stops = self.__build_parent_stops(
                stops,
                stop_times,
                trips,
                routes
            )
        else:
            stops = self.__filter_unused_stops(stops, stop_times)
            processed_stops = self.__build_unique_stops(
                stops,
                stop_times,
                trips,
                routes
            )

        return _Dataset(
            calendar=calendar,
            calendar_dates=calendar_dates,
            route_short_name_to_id=route_short_name_to_id,
            trip_id_to_info=trip_id_to_info,
            stop_id_to_departures=stop_id_to_departures,
            trip_id_to_stop_sequence=trip_id_to_stop_sequence,
            trip_id_to_stop_times=trip_id_to_stop_times,
            stop_id_to_coords=stop_id_to_coords,
            stops_tree=tree
        ), agency_name_to_dataset_name, processed_stops
    
# End of file gtfs_service.py
