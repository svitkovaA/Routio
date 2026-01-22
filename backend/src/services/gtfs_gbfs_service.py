from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Set, Tuple
import httpx
import pandas as pd
from zoneinfo import ZoneInfo
from models.types import OtherDeparture, Departures

calendar: pd.DataFrame
calendar_dates: pd.DataFrame
routes_dict = {}                                                # Maps route_short_name to route_id
trips_dict = {}                                                 # Maps trip_id to {route_id, service_id, headsign}
stop_to_trips_dict: defaultdict[str, List[Tuple[str, str]]] = defaultdict(list)    # Maps stop_id to list of (trip_id, departure_time)
colors_dict: Dict[str, str | None] = {}                         # Maps route_id to route_color, used in case lissy is unavailable
services_cache: Dict[date, Set[str]] = {}                       # Maps ref_date to set(service_id)

def load_gtfs_data(gtfs_path: str = "../datasets/gtfs"):
    print("function: load_gtfs_data")
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
    print("function: get_color")
    global routes_dict, colors_dict

    # Map public_code to route_id or None
    route_id = routes_dict.get(public_code)
    if route_id:
        return colors_dict.get(route_id)
    return None

def valid_services_for_date(ref_date: date) -> Set[str]:
    print("function: valid_services_for_date")
    global services_cache, calendar, calendar_dates

    # Result from cache
    if ref_date in services_cache:
        return services_cache[ref_date]

    # Map date to day of the week
    weekday = ref_date.strftime("%A").lower()

    # Services at given date
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

    # Add / remove exceptional services based on exception_type
    services.update(added)
    services.difference_update(removed)

    # Add services to cache
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
            {"departureTime": dep["departure_time"], "direction": dep["direction"]}
            for dep in final_departures
        ],
        "currentIndex": current_index,
    }

# GBFS URLs for Brno, Hodonin, Kahan
station_information_urls = {
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_te/cs/station_information.json",
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_nh/cs/station_information.json",
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_oc/cs/station_information.json"
}

# Maps station_id to capacity
bike_station_capacities: defaultdict[str, int | None] = defaultdict(lambda: None)

def load_gbfs_data() -> None:
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
