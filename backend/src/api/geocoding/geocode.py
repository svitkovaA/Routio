"""
file: geocode.py

Geocoding API endpoints, including forward and reverse geocoding.
"""

from fastapi import Query, APIRouter
from api.geocoding.nominatim_geocoder import NominatimGeocoder
from api.geocoding.photon_geocoder import PhotonGeocoder

# Router instance for geocoding endpoints
router = APIRouter(prefix="/geocode")

# Geocoder service instances
photon = PhotonGeocoder()
nominatim = NominatimGeocoder()

@router.get("/name")
async def geocode_name(
    q: str = Query(..., description="Partial address or place name"),
    limit: int = Query(5, description="Number of suggestions")
):
    """
    Performs forward geocoding.

    Args:
        q: Partial address or place name provided by user
        limit: Maximum number of suggestions to return

    Returns:
        List of suggestions
    """
    return await photon.geocode(q, limit)


@router.get("/latLon")
async def geocode_lat_lon(
    lat: float = Query(..., description="Latitude"), 
    lon: float = Query(..., description="Longitude")
):
    """
    Performs reverse geocoding.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees

    Returns:
        Dictionary containing formatted address information
    """
    return await nominatim.reverse(lat, lon)

# End of file geocode.py
