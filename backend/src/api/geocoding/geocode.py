"""
file: geocode.py

Geocoding API endpoints, including:
- geocoding of place names or addresses to geographic coordinates using Photon API,
- reverse geocoding of geographic coordinates to the addresses using Nominatim API.
"""

from fastapi import Query, APIRouter
from api.geocoding.nominatim_geocoder import NominatimGeocoder
from api.geocoding.photon_geocoder import PhotonGeocoder

router = APIRouter(prefix="/geocode")
photon = PhotonGeocoder()
nominatim = NominatimGeocoder()

@router.get("/name")
async def geocode_name(
    q: str = Query(..., description="Partial address or place name"),
    limit: int = Query(5, description="Number of suggestions")
):
    return await photon.geocode(q, limit)


@router.get("/latLon")
async def geocode_lat_lon(
    lat: float = Query(..., description="Latitude"), 
    lon: float = Query(..., description="Longitude")
):
    return await nominatim.reverse(lat, lon)

# End of file geocode.py
