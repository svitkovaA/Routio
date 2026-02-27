import asyncio
from dataclasses import dataclass
import os
import shutil
from typing import DefaultDict, Dict, List, Set, Tuple
import zipfile
import pandas as pd
from datetime import date, datetime
from collections import defaultdict
from zoneinfo import ZoneInfo
import requests
from config.datasets import GTFS_PATH, GTFS_URL
from models.route import Departure, OtherDeparture, OtherOptions
from service.service_base import ServiceBase

@dataclass(frozen=True)
class _GTFSState:
    calendar: pd.DataFrame
    calendar_dates: pd.DataFrame

    # Maps route_short_name to route_id
    routes_dict: Dict[str, str]

    # Maps trip_id to {route_id, service_id, headsign}
    trips_dict: Dict[int, Dict[str, str]]

    # Maps stop_id to list of (trip_id, departure_time)
    stop_to_trips_dict: DefaultDict[str, List[Tuple[int, str]]]

    # Maps route_id to route_color, used in case lissy is unavailable
    colors_dict: Dict[str, str | None]

class GTFSService(ServiceBase[_GTFSState]):
    def __init__(self):
        super().__init__()
        self.__lock = asyncio.Lock()

        # Maps ref_date to set(service_id)
        self.__services_cache: Dict[date, Set[str]] = {}

    def get_color(
        self,
        public_code: str
    ) -> None | str:
        """
        Retrieve the color associated with a public transport route
        
        Args:
            public_code: Public route identifier (route_short_name)

        Return:
            The route color in hexadecimal format or None if route or its colors is not available
        """
        
        state = self._get_state()
        route_id = state.routes_dict.get(public_code)
        return state.colors_dict.get(route_id) if route_id else None

    def get_departures_via(
        self,
        from_stop_id: str,
        to_stop_id: str, 
        route_short_name: str, 
        aimed_start_time: datetime, 
        n_prev: int = 4, 
        n_next: int = 20
    ) -> OtherOptions:
        """
        Returns departures for the given route
        
        Args:
            from_stop_id: The identifier of the origin stop
            to_stop_id: The identifier of the destination stop
            route_short_name: The public code
            aimed_start_time: Reference time in ISO format
            n_prev: Number of departures before the reference time
            n_next: Number of departures after the reference time
        
        Returns:
            Dictionary containing ordered list of departures and index of the currently selected departure
        """

        state = self._get_state()

        # Parse and normalize time to local timezone
        time_zone = ZoneInfo("Europe/Bratislava")
        ref_dt_local = (
            aimed_start_time.astimezone(time_zone) 
            if aimed_start_time.tzinfo
            else aimed_start_time.replace(tzinfo=time_zone)
        )
        ref_date = aimed_start_time.date()
        previous_date = ref_date - pd.Timedelta(days=1)
        next_date = ref_date + pd.Timedelta(days=1)

        # Get route_id from route_short_name
        route_id = state.routes_dict.get(route_short_name)
        if not route_id:
            return OtherOptions()
        
        valid_services_previous = self.__valid_services_for_date(state, previous_date)
        valid_services_today = self.__valid_services_for_date(state, ref_date)
        valid_services_next = self.__valid_services_for_date(state, next_date)

        # Trips containing destination stop
        trips_with_dest = {tid for tid, _ in state.stop_to_trips_dict.get(to_stop_id, [])}

        # Collect departures for previous, current and next day
        all_departures: List[OtherDeparture] = []
        for date, services in [
            (previous_date, valid_services_previous), 
            (ref_date, valid_services_today), 
            (next_date, valid_services_next)
        ]:
            departures = self.__collect_departures_for_date(
                state,
                from_stop_id,
                route_id,
                trips_with_dest,
                services
            )

            for departure in departures:
                # Converts GTFS time HH:MM:SS to YYYY-MM-DDTHH:MM:SStime_zone
                td = pd.to_timedelta(departure.departure_time_str)                           # type: ignore[type-arg]
                dt = datetime.combine(date, datetime.min.time(), tzinfo=time_zone) + td
                departure.departure_time = dt
            all_departures.extend(departures)

        # Sort departures by datetime
        all_departures.sort(key=lambda x: x.departure_time)

        # Find the first departure at or after reference time
        index = next((
            i 
            for i, dep in enumerate(all_departures) 
            if dep.departure_time >= ref_dt_local
        ), 0)

        MAX_GAP = pd.Timedelta(hours=2)

        # Collect previous departures
        previous: List[OtherDeparture] = []
        for i in list(reversed(range(index))):
            current = all_departures[i]
            # Insert first
            if not previous:
                previous.append(current)
                continue
            gap = previous[-1].departure_time - current.departure_time
            # Time gap is bigger than maximal allowed, rest is truncated
            if gap > MAX_GAP:
                break
            previous.append(current)
            # Enough previous results found
            if len(previous) >= n_prev:
                break
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
            if gap > MAX_GAP:
                break
            nexts.append(current)
            # Enough next results found
            if len(nexts) >= n_next:
                break

        # Combine previous and next departures
        final_departures = previous + nexts
        current_index = len(previous) if nexts else len(previous) - 1

        # Return departures with additional information
        return OtherOptions(
            departures=[
                Departure(
                    departureTime=dep.departure_time,
                    direction=dep.direction,
                    tripId=int(dep.trip_id)
                )
                for dep in final_departures
            ],
            currentIndex=current_index
        )
        
    async def reload(self) -> None:
        print("Loading GTFS cache")
        new_state = await asyncio.to_thread(self.__load_new_state)

        async with self.__lock:
            self._set_state(new_state)
            self.__services_cache.clear()
    
    def __valid_services_for_date(
        self,
        state: _GTFSState,
        ref_date: date
    ) -> Set[str]:
        """
        Determine all GTFS service IDs valid for a given date
        
        Args:
            ref_date: Reference date for which valid services are requested

        Returns:
            Set of service_id strings active on the given day
        """

        cached = self.__services_cache.get(ref_date)
        if cached is not None:
            return cached

        # Map date to day of the week
        weekday = ref_date.strftime("%A").lower()

        ymd = int(ref_date.strftime("%Y%m%d"))

        # Select services active on the given date and within the date range
        services = state.calendar[
            (state.calendar[weekday] == 1) &
            (state.calendar["start_date"] <= ymd) &
            (state.calendar["end_date"] >= ymd)
        ]["service_id"].tolist()

        # Remove duplicities
        services_set = set(services)

        # Handle exceptional services at given date
        exceptions = state.calendar_dates[state.calendar_dates["date"] == ymd]
        added = exceptions[exceptions["exception_type"] == 1]["service_id"].tolist()
        removed = exceptions[exceptions["exception_type"] == 2]["service_id"].tolist()

        # Add/remove exceptional services based on exception_type
        services_set.update(added)
        services_set.difference_update(removed)

        # Store the result in cache for future queries
        self.__services_cache[ref_date] = services_set
        return services_set

    @staticmethod
    def __collect_departures_for_date(
        state: _GTFSState,
        from_stop_id: str,
        route_id: str,
        trips_with_dest: Set[int],
        valid_service: Set[str]
    ) -> List[OtherDeparture]:
        departures: List[OtherDeparture] = []
        for trip_id, departure_time in state.stop_to_trips_dict.get(from_stop_id, []):
            trip_info = state.trips_dict.get(trip_id)
            if not trip_info:
                continue

            # Correct route
            if trip_info["route_id"] != route_id:
                continue

            # Service active on the given date
            if trip_info["service_id"] not in valid_service:
                continue
            
            # Service reaches destination stop
            if trip_id not in trips_with_dest:
                continue

            departures.append(
                OtherDeparture(
                    trip_id=trip_id,
                    departure_time=datetime.min,        # Dummy value
                    direction=trip_info.get("headsign", ""),
                    departure_time_str=departure_time
                )
            )

        return departures
    
    def __load_new_state(self) -> _GTFSState:
        """
        Loads and preprocess selected GTFS CSV data files into global in-memory structures
        """

        if os.path.exists(GTFS_PATH):
            shutil.rmtree(GTFS_PATH)
        os.makedirs(GTFS_PATH, exist_ok=True)

        zip_path = os.path.join(GTFS_PATH, "gtfs.zip")
        response = requests.get(GTFS_URL, timeout=60)
        response.raise_for_status()

        with open(zip_path, "wb") as f:
            f.write(response.content)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(GTFS_PATH)

        os.remove(zip_path)

        # Load GTFS CSV files
        calendar = pd.read_csv(f"{GTFS_PATH}/calendar.txt")                             # type: ignore[type-arg]
        calendar_dates = pd.read_csv(f"{GTFS_PATH}/calendar_dates.txt")                 # type: ignore[type-arg]
        stop_times: pd.DataFrame = pd.read_csv(f"{GTFS_PATH}/stop_times.txt")           # type: ignore[type-arg]
        trips: pd.DataFrame = pd.read_csv(f"{GTFS_PATH}/trips.txt")                     # type: ignore[type-arg]
        routes: pd.DataFrame = pd.read_csv(f"{GTFS_PATH}/routes.txt")                   # type: ignore[type-arg]

        # Map route_short_name to route_id
        routes_dict: Dict[str, str] = dict(
            zip(routes["route_short_name"], routes["route_id"])
        )

        # Map trip_id to {route_id, service_id, headsign}
        trips_dict: Dict[int, Dict[str, str]] = {
            int(row["trip_id"]): {
                "route_id": row["route_id"],
                "service_id": row["service_id"],
                "headsign": row.get("trip_headsign", "")
            }
            for _, row in trips.iterrows()
        }

        # Map stop_id to list of (trip_id, departure_time)
        stop_to_trips_dict: DefaultDict[str, List[Tuple[int, str]]] = defaultdict(list)
        for _, row in stop_times.iterrows():
            stop_to_trips_dict[row["stop_id"]].append((
                int(row["trip_id"]), 
                row["departure_time"]
            ))

        # Map route_id to route_color, used in case lissy is unavailable
        colors_dict: Dict[str, str | None] = {}
        for _, row in routes.iterrows():
            color = row.get("route_color")
            if pd.notna(color):
                color = f"#{str(color)}"
            else:
                color = None
            colors_dict[row["route_id"]] = color

        return _GTFSState(
            calendar=calendar,
            calendar_dates=calendar_dates,
            routes_dict=routes_dict,
            trips_dict=trips_dict,
            stop_to_trips_dict=stop_to_trips_dict,
            colors_dict=colors_dict
        )
