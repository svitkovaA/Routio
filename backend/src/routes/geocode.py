"""
file: geocode.py

Geocoding API endpoints, including:
- geocoding of place names or addresses to geographic coordinates using Photon API
- reverse geocoding of geographic coordinates to the addresses using Nominatim API
"""

from typing import Any, Dict, List
from fastapi import HTTPException, Query, APIRouter
import httpx
from models.types import Suggestion
from utils.geo import merge_close_results
from config import NOMINATIM_URL, PHOTON_URL

router = APIRouter(prefix="/geocode")

@router.get("/name")
async def geocode_name(
    q: str = Query(..., description="Partial address or place name"),
    limit: int = Query(5, description="Number of suggestions")
):
    """
    Performs geocoding for a given place name or address using Photon API

    Args:
        q: Address or place name used as the geocoding query
        limit: Maximum number of suggestion returned to the client

    Returns:
        A list of location suggestions or error if the request fails
    """
    print("endpoint: geocode_name")

    # Bounding box restricting the search area (South Moravian Region)
    bbox = "15.7,48.8,16.7,49.3"

    # Configure HTTP timeout and headers for the API request 
    timeout = httpx.Timeout(10.0)
    headers = {
        "User-Agent": "GreenGo/1.0 (academic project)"
    }

    # Request the Photon geocoding API
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        try:
            r = await client.get(PHOTON_URL, params={
                "q": q,
                # Request more results than needed to allow post-filtering
                "limit": limit * 3,
                "lang": "en",
                "bbox": bbox
            })
            r.raise_for_status()
            data = r.json()
        
        # Handle errors when connecting to Photon API
        except httpx.ReadTimeout:
            return {"error": "Timeout connecting to Photon API"}
        except httpx.HTTPStatusError as e:
            return {"error": f"Photon API error: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
        
    # Transform Photon response into internal suggestion format
    suggestions: List[Suggestion] = []
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

    # Remove spatially close or duplicate suggestions and limit results
    filtered_suggestions = merge_close_results(suggestions)[:limit]

    return filtered_suggestions

@router.get("/latLon")
async def geocode_lat_lon(
    lat: float = Query(..., description="Latitude"), 
    lon: float = Query(..., description="Longitude")
) -> Dict[str, Any]:
    """
    Performs reverse geocoding for given geographic coordinates using Nominatim API

    Args:
        lat: Latitude of the queried position
        lon: Longitude of the queried position

    Returns:
        Dictionary containing address information and geographic coordinates
        or error if request fails
    """
    print("endpoint: geocode_lat_lon")

    # Parameters for the Nominatim reverse geocoding request
    params: Dict[str, str | float] = {
        "format": "json",
        "lat": lat,
        "lon": lon,
        "addressdetails": 1,
        "zoom": 18
    }

    # Configure HTTP timeout for the API request
    timeout = httpx.Timeout(10.0)

    # Query the Nominatim reverse geocoding API
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(NOMINATIM_URL, params=params)
            r.raise_for_status()
            data = r.json()
        
        # Handle errors
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code = 500,
                detail = "Timeout connecting to Nominatim API"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code = 500,
                detail = f"Nominatim API error: {e.response.status_code}"
            )
        except Exception as e:
            raise HTTPException(
                status_code = 500,
                detail = f"Unexpected error: {str(e)}"
            )

    # Extract address information from the response
    address = data.get("address", {})

    return {
        "name": data.get("display_name"),
        "city": address.get("city") or address.get("town") or address.get("village"),
        "street": address.get("road", "") + ((" " + address.get("house_number")) if not address.get("road") and address.get("house_number") else ""),
        "lat": float(data.get("lat")),
        "lon": float(data.get("lon"))
    }

# End of file geocode.py
