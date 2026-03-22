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
from config.datasets import GTFS_DATASETS, GTFS_DIR, GTFS_DATASET
from models.route import TZ, Departure, OtherDeparture, OtherOptions
from service.service_base import ServiceBase
from sklearn.neighbors import BallTree

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

class GTFSService(ServiceBase[_GTFSState]):
    """
    Service responsible for downloading, parsing and processing GTFS data
    """
    def __init__(self):
        super().__init__()
        # Ensures safe concurrent reload access
        self.__lock = asyncio.Lock()

        # Maps dataset name to reference_date to set(service_id)
        self.__services_cache: Dict[str, Dict[date, Set[str]]] = {}

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

        # Prepare state dicts
        for (dataset_obj, agency_map), dataset_cfg in zip(results, GTFS_DATASETS):
            dataset_name = dataset_cfg["name"]
            datasets[dataset_name] = dataset_obj

            # Join agency maps
            for agency_name, ds_name in agency_map.items():

                # Duplicities found
                if agency_name in agency_name_to_dataset_name:
                    print(f"WARNING: duplicate agency_name '{agency_name}'")

                agency_name_to_dataset_name[agency_name] = ds_name

        new_state = _GTFSState(
            datasets=datasets,
            agency_name_to_dataset_name=agency_name_to_dataset_name
        )

        # Ensure atomic state swap
        async with self.__lock:
            self._set_state(new_state)
            self.__services_cache.clear()
    
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
    
    def __load_new_state(
        self,
        dataset: GTFS_DATASET
    ) -> Tuple[_Dataset, Dict[str, str]]:
        """
        Loads and preprocess the GTFS dataset.

        Args:
            dataset: GTFS dataset configuration

        Returns:
            Initialized _GTFSState instance
        """

        path = GTFS_DIR / self._hash_label(dataset["name"])

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
        ), agency_name_to_dataset_name
    
# End of file gtfs_service.py
