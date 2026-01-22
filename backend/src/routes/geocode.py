from fastapi import Query, APIRouter
import httpx
from utils.geo import merge_close_results
from config import NOMINATIM_URL, PHOTON_URL

router = APIRouter(prefix="/geocode")

@router.get("/name")
async def geocode_name(q: str = Query(..., description="Partial address or place name"), limit: int = Query(5, description="Number of suggestions")):
    print("endpoint: geocode_name")
    bbox = "15.7,48.8,16.7,49.3"

    timeout = httpx.Timeout(10.0)
    headers = {
        "User-Agent": "GreenGo/1.0 (academic project)"
    }
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        try:
            r = await client.get(PHOTON_URL, params={
                "q": q,
                "limit": limit * 3,
                "lang": "en",
                "bbox": bbox
            })
            r.raise_for_status()
            data = r.json()
        except httpx.ReadTimeout:
            return {"error": "Timeout connecting to Photon API"}
        except httpx.HTTPStatusError as e:
            return {"error": f"Photon API error: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
        
    suggestions = []
    for feature in data.get("features", []):
        coords = feature["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]
        props = feature["properties"]
        suggestions.append({
            "name": props.get("name"),
            "type": props.get("type"),
            "country": props.get("country"),
            "city": props.get("city"),
            "street": props.get("street"),
            "lat": lat,
            "lon": lon
        })


    filtered_suggestions = merge_close_results(suggestions)[:limit]

    return filtered_suggestions

@router.get("/latLon")
async def geocode_lat_lon(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude")):
    print("endpoint: geocode_lat_lon")
    params = {
        "format": "json",
        "lat": lat,
        "lon": lon,
        "addressdetails": 1,
        "zoom": 18
    }

    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(NOMINATIM_URL, params=params)
            r.raise_for_status()
            data = r.json()
        except httpx.ReadTimeout:
            return {"error": "Timeout connecting to Nominatim API"}
        except httpx.HTTPStatusError as e:
            return {"error": f"Nominatim API error: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    address = data.get("address", {})
    return {
        "name": data.get("display_name"),
        "city": address.get("city") or address.get("town") or address.get("village"),
        "street": address.get("road", "") + ((" " + address.get("house_number")) if not address.get("road") and address.get("house_number") else ""),
        "lat": float(data.get("lat")),
        "lon": float(data.get("lon"))
    }
