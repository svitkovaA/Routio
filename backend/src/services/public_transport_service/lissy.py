"""
file: lissy.py

Functions for caching and retrieving information about shapes and historical delays retrieved from Lissy API
"""

import asyncio
from datetime import date as d, timedelta, datetime
from types import CoroutineType
from typing import Any, Dict, List, Tuple
import httpx
from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from models.types import LissyAvailableRoute, LissyDelayTrips, LissyShape, LissyShapes, LissyTrips, RouteData
from config import LISSY_API_KEY, LISSY_URL

# Size of the cache window
CACHE_DAYS = 7

# The maximum number of shape information in LRU cache
MAX_SHAPE_CACHE_SIZE = 5000

shapes_cache: Dict[str, Dict[str, LissyShapes]] = {}                    # Maps route_short_name to route_color and trips
routes_cache: Dict[str, Dict[str, RouteData]] = {}                      # Maps route_short_name to route_data
shape_detail_cache: OrderedDict[int, LissyShape] = OrderedDict()        # Maps shape_id to shape_data (LRU)
lissy_client = httpx.AsyncClient(timeout=10, headers={"Authorization": LISSY_API_KEY}) 

# Caching functions
async def lissy_status(date: d) -> bool:
    print("function: lissy_status")
    try:
        url = LISSY_URL + "shapes/getShapes"
        api_date = f"{date.year}-{date.month - 1}-{date.day}"
        r = await lissy_client.get(url, params={"date": api_date})
        r.raise_for_status()
        r.json()
    except Exception:
        return False
    return True

def get_cache_window(today: d) -> List[str]:
    """
    Docstring for get_cache_window
    
    Args:
        today: Reference date from which the cache window is computed

    Returns:
        List of dates in ISO format

    """
    print("function: get_cache_window")
    return [ (today - timedelta(days=i)).isoformat() for i in range(CACHE_DAYS) ]

async def get_shapes(date: d) -> list[LissyShapes] | None:
    """
    Fetches route shapes for the given date
    
    Args:
        date: Date for which route shapes should be retrieved

    Returns:
        A list of route shapes if success, None otherwise
    """
    print("function: get_shapes")
    try:
        url = LISSY_URL + "shapes/getShapes"
        api_date = f"{date.year}-{date.month - 1}-{date.day}"
        r = await lissy_client.get(url, params={"date": api_date})
        r.raise_for_status()
        data: List[LissyShapes] = r.json()
    except Exception:
        return None
    return data
 
async def build_routes_map(routes_list: List[LissyAvailableRoute], cache_window: list[str]):
    """
    Builds and caches stop_label to shape_id, stopOrder and trips_by_time map

    Args:
        routes_list: List of available routes returned by Lissy API
        cache_window: List of dates in ISO format
    """
    print("function: build_routes_map")
    global routes_cache

    # Build date range required for the delay API
    start_date = (datetime.fromisoformat(cache_window[3]) - relativedelta(months=1))
    end_date = (datetime.fromisoformat(cache_window[1]) - relativedelta(months=1))
    start_str = f"{start_date.year}-{start_date.month}-{start_date.day}"
    end_str = f"{end_date.year}-{end_date.month}-{end_date.day}"

    async def fetch_route_data(route: LissyAvailableRoute) -> Tuple[str, Dict[str, RouteData]]:
        """
        Fetch trip data for delay from Lissy API
        
        Args:
            route: Route descriptor
        
        Returns:
            A tuple, including route_short_name and route_data
        """
        route_id = route["id"]
        short_name = route["route_short_name"]

        # Fetch available trips for the selected date range
        try:
            # Returns shape id, stops and trips
            url = LISSY_URL + "delayTrips/getAvailableTrips"
            r = await lissy_client.get(url, params={ "dates": f'[["{start_str}","{end_str}"]]', "route_id": route_id, "fullStopOrder": True})
            r.raise_for_status()
            data: List[LissyDelayTrips] = r.json()

            route_data: Dict[str, RouteData] = {}
            for shape in data:
                shape_id = shape.get("shape_id")
                stops_label = shape.get("stops") or f"shape_{shape_id}"
                stop_order = shape.get("stopOrder", [])
                trips: List[LissyTrips] = shape.get("trips", [])

                # Maps departure time to trip_id
                trips_by_time: dict[str, int] = {}
                for trip in trips:
                    dep_time = trip.get("dep_time")
                    trip_id = trip.get("id")

                    if dep_time is not None and trip_id is not None:
                        trips_by_time[dep_time] = trip_id

                # From stop label get information
                route_data[stops_label] = {
                    "shape_id": shape_id,
                    "stopOrder": stop_order,
                    "trips_by_time": trips_by_time,
                }

            return short_name, route_data

        except Exception:
            return short_name, {}

    # Fetch route data concurrently
    results = await asyncio.gather(*[fetch_route_data(route) for route in routes_list])

    # Store non empty data to cache
    for short_name, route_data in results:
        if route_data:
            routes_cache[short_name] = route_data

async def cache_lissy() -> None:
    """
    Cache available shapes for the date range and available trips for delay visualisation  
    """
    print("function: cache_lissy")
    global shapes_cache

    # Determine the date window to cache
    cache_window = get_cache_window(d.today())

    # Prepare async tasks for fetching shapes for each date
    tasks: List[CoroutineType[Any, Any, list[LissyShapes] | None]] = []
    for day_str in cache_window:
        day = datetime.fromisoformat(day_str).date()
        tasks.append(get_shapes(day))

    # Execute shape requests concurrently
    results = await asyncio.gather(*tasks)

    # Store shapes in cache indexed by date
    for day_str, shapes in zip(cache_window, results):
        if shapes:
            # Maps route short name to route_color and trips
            shapes_cache[day_str] = {shape["route_short_name"]: shape for shape in shapes}

    # Months in lissy are in format 0-11
    cache_window_minus_month: List[str] = []
    for date_str in cache_window:
        dt = datetime.fromisoformat(date_str) - relativedelta(months=1)
        cache_window_minus_month.append(f"{dt.year}-{dt.month}-{dt.day}")

    # Try to fetch routes for which the delays are available
    try:
        # Example of dates_param format '[["2025-9-8","2025-9-10"]]'
        dates_param = f'[["{cache_window_minus_month[3]}","{cache_window_minus_month[1]}"]]'
        url = LISSY_URL + "delayTrips/getAvailableRoutes"
        r = await lissy_client.get(url, params={"dates": dates_param})
        r.raise_for_status()
    except Exception:
        return

    # Cache and build stop_label to shape_id, stopOrder and trips_by_time map
    await build_routes_map(r.json(), cache_window)

# Retrieving information about delays
def get_trip_id_by_time(route_short_name: str, stops_label: str, dep_time: str) -> int | None:
    """
    Finds a trip matching a given departure time for a specific route

    Args:
        route_short_name: The public code
        stops_label: Identifier representing origin->destination
        dep_time: The departure time

    Returns:
        Trip_id if the matching trip is found, None otherwise
    """
    print("function: get_trip_id_by_time")
    # Normalize datetime ISO format to HH:MM:SS
    if "T" in dep_time:
        try:
            dep_time = datetime.fromisoformat(dep_time).strftime("%H:%M:%S")
        except ValueError:
            return None
        
    # Retrieve cached route data
    route_data = routes_cache.get(route_short_name)
    if not route_data:
        return None

    shape_data = route_data.get(stops_label)
    if not shape_data:
        return None

    trips_by_time = shape_data.get("trips_by_time", {})
    if not trips_by_time:
        return None

    # Search for the closest matching trip within tolerance
    target_dt = datetime.strptime(dep_time, "%H:%M:%S")
    best_trip = None
    smallest_diff = timedelta(hours=24)
    tolerance_min = 5

    # Find closest trip to given time in the future
    for time_str, trip_id in trips_by_time.items():
        try:
            trip_dt = datetime.strptime(time_str, "%H:%M:%S")
        except ValueError:
            continue

        diff = (trip_dt - target_dt).total_seconds()

        # Accept only future departures within the tolerance window
        if 0 <= diff <= tolerance_min * 60 and diff < smallest_diff.total_seconds():
            smallest_diff = timedelta(seconds=diff)
            best_trip = trip_id

    # Return only one trip which is the closest to the given time in the future
    if best_trip:
        return best_trip
    
    return None

async def get_delays(trip_id: int, index: int) -> Dict[str, int] | None:
    """
    Retrieves historical delays for a specific trip and stop index
    
    Args:
        trip_id: The identifier of the trip
        index: Index of the stop within the trip for which the delay should be extracted

    Returns:
        A map with date strings and delay values
    """

    # Create a cache window in the format required by Lissy API
    cache_window_minus_month: List[str] = []
    for date_str in get_cache_window(d.today()):
        dt = datetime.fromisoformat(date_str) - relativedelta(months=1)
        cache_window_minus_month.append(f"{dt.year}-{dt.month}-{dt.day}")

    dates_param = f'[["{cache_window_minus_month[3]}","{cache_window_minus_month[1]}"]]'
    url = LISSY_URL + "delayTrips/getTripData"

    # Fetch delay data for the given trip
    try:
        r = await lissy_client.get(url, params={"dates": dates_param, "trip_id": trip_id})
        r.raise_for_status()
        data: Dict[str, Dict[str, Dict[str, int]]] = r.json()
        delays: dict[str, int] = {}
        for date, delay in data.items():
            delay_data = delay[str(index)]
            value = list(delay_data.values())[0]
            delays[date] = value
        return delays
    except Exception:
        return None

# Retrieving information about shapes
def get_date(today: d, date: d) -> d:
    """
    Normalizes a date to fit within the cache window
    
    Args:
        today: The reference date
        date: Date to be normalized to the cache window
    
    Returns:
        A date that is less than or equal to the reference date and aligned
        with the cache window size
    """
    print("function: get_date")
    while date > today:
        date -= timedelta(days=CACHE_DAYS)
    return date

async def get_shapes_cached(date: d) -> Dict[str, LissyShapes]:
    """
    Returns cached route shape data for a given date

    Args:
        date: Date for which route shape data are requested
    
    Returns:
        A map containing route_short_name and shape_data
    """
    print("function: get_shapes_cached")
    today = d.today()

    # Normalize date to fit into cache window
    date = get_date(today, date)
    date_str = date.isoformat()

    # Determine currently valid cache dates
    valid_dates = get_cache_window(today)
    
    # Remove old cached data
    for key in list(shapes_cache.keys()):
        if key not in valid_dates:
            shapes_cache.pop(key)

    # Return cached shapes if available
    if date_str in shapes_cache:
        return shapes_cache[date_str]
    
    # Fetch and cache data if not already present
    shapes = await get_shapes(date)
    if shapes:
        shapes_cache[date_str] = {shape["route_short_name"]: shape for shape in shapes}

    return shapes_cache.get(date_str, {})

async def get_shape(shape_id: int) -> LissyShape | None:
    """
    Retrieves detailed shape geometry for a given shape_id

    Args:
        shape_id:  Identifier of the shape whose geometry is requested

    Returns:
        Shape geometry data if available, None otherwise
    """
    print("function: get_shape")

    # Return shape from cache if available (LRU update)
    if shape_id in shape_detail_cache:
        shape_detail_cache.move_to_end(shape_id)
        return shape_detail_cache[shape_id]
    
    # Fetch shape if not already present
    try:
        url = LISSY_URL + "shapes/getShape"
        r = await lissy_client.get(url, params={"shape_id": shape_id})
        r.raise_for_status()
        data: LissyShape = r.json()
    except Exception:
        return None
        
    # Store fetched shape in cache
    shape_detail_cache[shape_id] = data
    shape_detail_cache.move_to_end(shape_id)

    # Enforce maximum cache size (LRU eviction)
    if len(shape_detail_cache) > MAX_SHAPE_CACHE_SIZE:
        shape_detail_cache.popitem(last=False)

    return data

# End of file lissy.py
