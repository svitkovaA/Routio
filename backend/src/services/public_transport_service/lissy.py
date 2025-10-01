from datetime import date as d, timedelta, datetime
import json
import httpx
from collections import OrderedDict
from config import LISSY_API_KEY, LISSY_URL


CACHE_DAYS = 7
MAX_SHAPE_CACHE_SIZE = 5000

shapes_cache = {}
shape_detail_cache: "OrderedDict[int, dict]" = OrderedDict()
lissy_client = httpx.AsyncClient(timeout=10, headers={"Authorization": LISSY_API_KEY})

async def lissy_status(date: d):
    print("function: lissy_status")
    try:
        url = LISSY_URL + "shapes/getShapes"
        api_date = f"{date.year}-{date.month - 1}-{date.day}"
        r = await lissy_client.get(url, params={"date": api_date})
        r.raise_for_status()
        data = r.json()
    except Exception:
        return False
    return True

async def cache_lissy():
    print("function: cache_lissy")
    global shapes_cache
    cache_window = get_cache_window(d.today())
    for day_str in cache_window:
        day = datetime.fromisoformat(day_str).date()
        shapes = await get_shapes(day)
        if shapes:
            shapes_cache[day_str] = {shape["route_short_name"]: shape for shape in shapes}

def get_cache_window(today: d):
    print("function: get_cache_window")
    return { (today - timedelta(days=i)).isoformat() for i in range(CACHE_DAYS) }

def get_date(today: d, date: d):
    print("function: get_date")
    while date > today:
        date -= timedelta(days=CACHE_DAYS)
    return date

async def get_shapes_cached(date: d):
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

async def get_shapes(date: d):
    print("function: get_shapes")
    try:
        url = LISSY_URL + "shapes/getShapes"
        api_date = f"{date.year}-{date.month - 1}-{date.day}"
        r = await lissy_client.get(url, params={"date": api_date})
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None
    return data
 
async def get_shape(shape_id): 
    print("function: get_shape")
    if shape_id in shape_detail_cache:
        shape_detail_cache.move_to_end(shape_id)
        return shape_detail_cache[shape_id]
    
    try:
        url = LISSY_URL + "shapes/getShape"
        r = await lissy_client.get(url, params={"shape_id": shape_id})
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None
        
    shape_detail_cache[shape_id] = data
    shape_detail_cache.move_to_end(shape_id)

    if len(shape_detail_cache) > MAX_SHAPE_CACHE_SIZE:
        shape_detail_cache.popitem(last=False)

    return data
