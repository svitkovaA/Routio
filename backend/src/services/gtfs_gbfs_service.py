"""
file: gtfs_gbfs_service.py

Processing GTFS, GTFS-RT and GBFS files
"""

from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Set, Tuple, cast
import httpx
import pandas as pd
from zoneinfo import ZoneInfo
from models.types import Departure, OtherDeparture, Departures
from google.transit.gtfs_realtime_pb2 import FeedMessage        # type: ignore[import-untyped]
from config import GTFSRT_URL, station_information_urls

calendar: pd.DataFrame
calendar_dates: pd.DataFrame
routes_dict = {}                                                # Maps route_short_name to route_id
trips_dict = {}                                                 # Maps trip_id to {route_id, service_id, headsign}
stop_to_trips_dict: defaultdict[str, List[Tuple[str, str]]] = defaultdict(list)    # Maps stop_id to list of (trip_id, departure_time)
colors_dict: Dict[str, str | None] = {}                         # Maps route_id to route_color, used in case lissy is unavailable
services_cache: Dict[date, Set[str]] = {}                       # Maps ref_date to set(service_id)
vehicle_position_map: Dict[str, Tuple[float, float]] = {}       # Maps trip_id to (latitude, longitude)

def load_gtfs_data(gtfs_path: str = "../datasets/gtfs"):
    """
    Loads and preprocess selected GTFS CSV data files into global in-memory structures

    Args:
        gtfs_path: Path to the directory containing GTFS CSV files
    """
    print("function: load_gtfs_data")
    # Declares global variables which will store parsed GTFS data
    global calendar, calendar_dates, routes_dict, trips_dict, stop_to_trips_dict, colors_dict

    # Load GTFS CSV files
    calendar = pd.read_csv(f"{gtfs_path}/calendar.txt")                             # type: ignore[type-arg]
    calendar_dates = pd.read_csv(f"{gtfs_path}/calendar_dates.txt")                 # type: ignore[type-arg]
    stop_times: pd.DataFrame = pd.read_csv(f"{gtfs_path}/stop_times.txt")           # type: ignore[type-arg]
    trips: pd.DataFrame = pd.read_csv(f"{gtfs_path}/trips.txt")                     # type: ignore[type-arg]
    routes: pd.DataFrame = pd.read_csv(f"{gtfs_path}/routes.txt")                   # type: ignore[type-arg]

    # Map route_short_name to route_id
    routes_dict = dict(zip(routes["route_short_name"], routes["route_id"]))

    # Map trip_id to {route_id, service_id, headsign}
    trips_dict = {
        row["trip_id"]: {
            "route_id": row["route_id"],
            "service_id": row["service_id"],
            "headsign": row.get("trip_headsign", "")
        }
        for _, row in trips.iterrows()
    }

    # Map stop_id to list of (trip_id, departure_time)
    for _, row in stop_times.iterrows():
        stop_to_trips_dict[row["stop_id"]].append((row["trip_id"], row["departure_time"]))

    # Map route_id to route_color, used in case lissy is unavailable
    for _, row in routes.iterrows():
        color = row.get("route_color")
        if pd.notna(color):
            color = f"#{str(color)}"
        else:
            color = None
        colors_dict[row["route_id"]] = color

def get_color(public_code: str) -> None | str:
    """
    Retrieve the color associated with a public transport route
    
    Args:
        public_code: Public route identifier (route_short_name)

    Return:
        The route color in hexadecimal format or None if route or its colors is not available
    """
    print("function: get_color")
    global routes_dict, colors_dict

    # Map public_code to route_id or None
    route_id = routes_dict.get(public_code)
    if route_id:
        return colors_dict.get(route_id)
    return None

def valid_services_for_date(ref_date: date) -> Set[str]:
    """
    Determine all GTFS service IDs valid for a given date
    
    Args:
        ref_date: Reference date for which valid services are requested

    Returns:
        Set of service_id strings active on the given day
    """
    print("function: valid_services_for_date")
    # Access global GTFS data structures and cache
    global services_cache, calendar, calendar_dates

    # Return result from cache if available
    if ref_date in services_cache:
        return services_cache[ref_date]

    # Map date to day of the week
    weekday = ref_date.strftime("%A").lower()

    # Select services active on the given date and within the date range
    services = calendar[
        (calendar[weekday] == 1) &
        (calendar["start_date"] <= int(ref_date.strftime("%Y%m%d"))) &
        (calendar["end_date"] >= int(ref_date.strftime("%Y%m%d")))
    ]["service_id"].tolist()

    # Remove duplicities
    services = set(services)

    # Handle exceptional services at given date
    exceptions = calendar_dates[calendar_dates["date"] == int(ref_date.strftime("%Y%m%d"))]
    added = exceptions[exceptions["exception_type"] == 1]["service_id"].tolist()
    removed = exceptions[exceptions["exception_type"] == 2]["service_id"].tolist()

    # Add/remove exceptional services based on exception_type
    services.update(added)
    services.difference_update(removed)

    # Store the result in cache for future queries
    services_cache[ref_date] = services
    return services

def get_departures_via(
    from_stop_id: str, 
    to_stop_id: str, 
    route_short_name: str, 
    aimed_start_time: str, 
    n_prev: int = 4, 
    n_next: int = 20
) -> Departures:
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
    print("function: get_departures_via")

    # Parse and normalize time to local timezone
    time_zone = ZoneInfo("Europe/Bratislava")
    ref_dt = datetime.fromisoformat(aimed_start_time)
    ref_dt_local = ref_dt.astimezone(time_zone) if ref_dt.tzinfo else ref_dt.replace(tzinfo=time_zone)
    ref_date = ref_dt.date()
    previous_date = ref_date - pd.Timedelta(days=1)
    next_date = ref_date + pd.Timedelta(days=1)

    # Get route_id from route_short_name
    route_id = routes_dict.get(route_short_name)
    if not route_id:
        return {"departures": [], "currentIndex": None}

    # Get valid services for the given date
    valid_services_previous = valid_services_for_date(previous_date)
    valid_services_today = valid_services_for_date(ref_date)
    valid_services_next = valid_services_for_date(next_date)

    # Trips containing destination stop
    trips_with_dest = {tid for tid, _ in stop_to_trips_dict.get(to_stop_id, [])}

    # Collect departures for given valid_service
    def collect_departures_for_date(valid_service: Set[str]) -> List[OtherDeparture]:
        departures: List[OtherDeparture] = []
        for trip_id, departure_time in stop_to_trips_dict.get(from_stop_id, []):
            trip_info = trips_dict.get(trip_id)
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

            departures.append({
                "trip_id": trip_id,
                "departure_time": departure_time,
                "direction": trip_info["headsign"],
                "departure_dt": datetime.min
            })
        return departures

    # Collect departures for previous, current and next day
    all_departures: List[OtherDeparture] = []
    for date, services in [(previous_date, valid_services_previous), (ref_date, valid_services_today), (next_date, valid_services_next)]:
        departures = collect_departures_for_date(services)
        for departure in departures:
            # Converts GTFS time HH:MM:SS to YYYY-MM-DDTHH:MM:SStime_zone
            td = pd.to_timedelta(departure["departure_time"])                           # type: ignore[type-arg]
            dt = datetime.combine(date, datetime.min.time(), tzinfo=time_zone) + td
            departure["departure_dt"] = dt
            departure["departure_time"] = dt.isoformat()
        all_departures.extend(departures)

    # Sort departures by datetime
    all_departures.sort(key=lambda x: x["departure_dt"])

    # Find the first departure at or after reference time
    index = next((i for i, dep in enumerate(all_departures) if dep["departure_dt"] >= ref_dt_local), 0)

    MAX_GAP = pd.Timedelta(hours=2)

    # Collect previous departures
    previous: List[OtherDeparture] = []
    for i in list(reversed(range(index))):
        current = all_departures[i]
        # Insert first
        if not previous:
            previous.append(current)
            continue
        gap = previous[-1]["departure_dt"] - current["departure_dt"]
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
        gap = current["departure_dt"] - nexts[-1]["departure_dt"]
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
    return {
    "departures": [
        cast(Departure, {
            "departureTime": dep["departure_time"],
            "direction": dep["direction"],
            "tripId": dep["trip_id"],
        })
        for dep in final_departures
    ],
    "currentIndex": current_index,
}

async def vehicle_position():
    """
    Fetch and parse GTFS-Realtime vehicle position data
    """
    print("function: vehicle_position")
    global vehicle_position_map

    # Fetch GTFS-Realtime feed
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(GTFSRT_URL)
        resp.raise_for_status()
        data = resp.content

    # Parse protobuf GTFS-RT message
    feed = FeedMessage()
    feed.ParseFromString(data)
    
    # Reset and update vehicle position map
    vehicle_position_map = {}

    for entity in feed.entity:
        # Process only vehicle position entities
        if entity.HasField("vehicle"):
            v = entity.vehicle

            # Skip entities without a valid trip ID
            if not (v.HasField("trip") and v.trip.trip_id):
                continue
            
            trip_id = v.trip.trip_id
            
            # Skip entities without valid position data
            if not (v.HasField("position") and v.position.latitude and v.position.longitude):
                continue
            
            # Store current vehicle position for the trip
            vehicle_position_map[trip_id] = (v.position.latitude, v.position.longitude)

def get_vehicle_position(trip_id: int) -> Tuple[float, float] | None:
    """
    Returns the latest known vehicle position for a given trip_id

    Args:
        trip_id: GTFS trip_id

    Returns:
        Tuple(latitude, longitude) if position is available, otherwise None
    """
    global vehicle_position_map
    return vehicle_position_map.get(str(trip_id))

# Maps station_id to capacity
bike_station_capacities: defaultdict[str, int | None] = defaultdict(lambda: None)

def load_gbfs_data() -> None:
    """
    Loads and preprocess GBFS data file station_information.json
    """
    print("function: load_gbfs_data")
    global station_information_urls, bike_station_capacities

    # Get station information
    for url in station_information_urls:
        response = httpx.get(url, timeout=10)
        response_data = response.json()
        stations = response_data.get("data", {}).get("stations", [])
        
        # Map station_id to capacity if provided
        for station in stations:
            capacity = station.get("capacity")
            if capacity is not None:
                bike_station_capacities[station["station_id"]] = capacity

# End of file gtfs_gbfs_service.py
