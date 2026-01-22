import asyncio
from datetime import date as d, timedelta, datetime
from types import CoroutineType
from typing import Any, Dict, List, Tuple
import httpx
from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from models.types import LissyAvailableRoute, LissyDelayTrips, LissyShape, LissyShapes, LissyTrips, RouteData
from config import LISSY_API_KEY, LISSY_URL

CACHE_DAYS = 7
MAX_SHAPE_CACHE_SIZE = 5000

shapes_cache: Dict[str, Dict[str, LissyShapes]] = {}
routes_cache: Dict[str, Dict[str, RouteData]] = {}
shape_detail_cache: OrderedDict[int, List[LissyShape]] = OrderedDict()
lissy_client = httpx.AsyncClient(timeout=10, headers={"Authorization": LISSY_API_KEY})

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

async def build_routes_map(routes_list: List[LissyAvailableRoute], cache_window: list[str]):
    print("function: build_routes_map")
    global routes_cache

    start_date = (datetime.fromisoformat(cache_window[3]) - relativedelta(months=1))
    end_date = (datetime.fromisoformat(cache_window[1]) - relativedelta(months=1))
    start_str = f"{start_date.year}-{start_date.month}-{start_date.day}"
    end_str = f"{end_date.year}-{end_date.month}-{end_date.day}"

    async def fetch_route_data(route: LissyAvailableRoute) -> Tuple[str, Dict[str, RouteData]]:
        route_id = route["id"]
        short_name = route["route_short_name"]
        try:
            # Returns shape id, stops and trips
            url = LISSY_URL + "delayTrips/getAvailableTrips"
            r = await lissy_client.get(url, params={ "dates": f'[["{start_str}","{end_str}"]]', "route_id": route_id, "fullStopOrder": True})
            # r = await lissy_client.get(url, params={ "dates": '[["2025-9-8","2025-9-10"]]', "route_id": route_id, "fullStopOrder": True})
            r.raise_for_status()
            data: List[LissyDelayTrips] = r.json()

            route_data: Dict[str, RouteData] = {}
            for shape in data:
                shape_id = shape.get("shape_id")
                stops_label = shape.get("stops") or f"shape_{shape_id}"
                stop_order = shape.get("stopOrder", [])
                trips: List[LissyTrips] = shape.get("trips", [])

                # From departure time get trip id
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

    results = await asyncio.gather(*[fetch_route_data(route) for route in routes_list])

    for short_name, route_data in results:
        if route_data:
            routes_cache[short_name] = route_data

def get_trip_id_by_time(route_short_name: str, stops_label: str, dep_time: str) -> int | None:
    print("function: get_trip_id_by_time")
    # Search in json
    if "T" in dep_time:
        try:
            dep_time = datetime.fromisoformat(dep_time).strftime("%H:%M:%S")
        except ValueError:
            return None
    route_data = routes_cache.get(route_short_name)
    if not route_data:
        return None

    shape_data = route_data.get(stops_label)
    if not shape_data:
        return None

    trips_by_time = shape_data.get("trips_by_time", {})
    if not trips_by_time:
        return None

    # 5 minute tolerance
    target_dt = datetime.strptime(dep_time, "%H:%M:%S")
    best_trip = None
    smallest_diff = timedelta(hours=24)
    tolerance_min = 5

    for time_str, trip_id in trips_by_time.items():
        try:
            trip_dt = datetime.strptime(time_str, "%H:%M:%S")
        except ValueError:
            continue

        diff = (trip_dt - target_dt).total_seconds()

        if 0 <= diff <= tolerance_min * 60 and diff < smallest_diff.total_seconds():
            smallest_diff = timedelta(seconds=diff)
            best_trip = trip_id

    if best_trip:
        return best_trip
    
    return None

async def get_delays(trip_id: int, index: int) -> Dict[str, int] | None:
    cache_window_minus_month: List[str] = []
    for date_str in get_cache_window(d.today()):
        dt = datetime.fromisoformat(date_str) - relativedelta(months=1)
        cache_window_minus_month.append(f"{dt.year}-{dt.month}-{dt.day}")

    dates_param = f'[["{cache_window_minus_month[3]}","{cache_window_minus_month[1]}"]]'
    # dates_param = '[["2025-9-8","2025-9-10"]]'
    url = LISSY_URL + "delayTrips/getTripData"
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

async def cache_lissy() -> None:
    print("function: cache_lissy")
    global shapes_cache
    cache_window = get_cache_window(d.today())
    tasks: List[CoroutineType[Any, Any, list[LissyShapes] | None]] = []
    for day_str in cache_window:
        day = datetime.fromisoformat(day_str).date()
        tasks.append(get_shapes(day))

    results = await asyncio.gather(*tasks)
    for day_str, shapes in zip(cache_window, results):
        if shapes:
            # From route short name get route color and trips
            shapes_cache[day_str] = {shape["route_short_name"]: shape for shape in shapes}

    # Months 0-11
    cache_window_minus_month: List[str] = []
    for date_str in cache_window:
        dt = datetime.fromisoformat(date_str) - relativedelta(months=1)
        cache_window_minus_month.append(f"{dt.year}-{dt.month}-{dt.day}")

    try:
        # Returns route short name and id
        dates_param = f'[["{cache_window_minus_month[3]}","{cache_window_minus_month[1]}"]]'
        # dates_param = '[["2025-9-8","2025-9-10"]]'
        url = LISSY_URL + "delayTrips/getAvailableRoutes"
        r = await lissy_client.get(url, params={"dates": dates_param})
        r.raise_for_status()
    except Exception:
        return

    await build_routes_map(r.json(), cache_window)

def get_cache_window(today: d) -> List[str]:
    print("function: get_cache_window")
    return [ (today - timedelta(days=i)).isoformat() for i in range(CACHE_DAYS) ]

def get_date(today: d, date: d) -> d:
    print("function: get_date")
    while date > today:
        date -= timedelta(days=CACHE_DAYS)
    return date

async def get_shapes_cached(date: d) -> Dict[str, LissyShapes]:
    print("function: get_shapes_cached")
    today = d.today()
    date = get_date(today, date)
    date_str = date.isoformat()
    valid_dates = get_cache_window(today)
    
    for key in list(shapes_cache.keys()):
        if key not in valid_dates:
            shapes_cache.pop(key)

    if date_str in shapes_cache:
        return shapes_cache[date_str]
    
    
    shapes = await get_shapes(date)
    if shapes:
        shapes_cache[date_str] = {shape["route_short_name"]: shape for shape in shapes}
    return shapes_cache.get(date_str, {})

async def get_shapes(date: d) -> list[LissyShapes] | None:
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
 
async def get_shape(shape_id: int) -> List[LissyShape] | None: 
    print("function: get_shape")
    if shape_id in shape_detail_cache:
        shape_detail_cache.move_to_end(shape_id)
        return shape_detail_cache[shape_id]
    
    try:
        url = LISSY_URL + "shapes/getShape"
        r = await lissy_client.get(url, params={"shape_id": shape_id})
        r.raise_for_status()
        data: List[LissyShape] = r.json()
    except Exception:
        return None
        
    shape_detail_cache[shape_id] = data
    shape_detail_cache.move_to_end(shape_id)

    if len(shape_detail_cache) > MAX_SHAPE_CACHE_SIZE:
        shape_detail_cache.popitem(last=False)

    return data
