"""
file: nominatim_geocoder.py

Implementation of reverse geocoding service using the Nominatim API.
"""

from api.geocoding.geocoder_base import GeocoderBase
from config.external import NOMINATIM_URL
from typing import Dict, Any

class NominatimGeocoder(GeocoderBase):
    """
    Reverse geocoder implementation using the Nominatim API.
    """
    def __init__(self):
        """
        Initializes Nominatim geocoder with configured base URL.
        """
        super().__init__(NOMINATIM_URL)

    async def reverse(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:
        """
        Performs reverse geocoding based on geographic coordinates.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            Dictionary containing location information
        """
        # Photon API call
        data = await self._get({
            "format": "json",
            "lat": lat,
            "lon": lon,
            "addressdetails": 1,
            "zoom": 18
        })

        # Extract structured address
        address = data.get("address", {})

        city = str(address.get("city") or address.get("town") or address.get("village"))
        street = str(address.get("road", "") + (
            (" " + address.get("house_number"))
            if not address.get("road") and address.get("house_number")
            else ""
        ))
        name = ", ".join([item for item in [street, city] if item])
        
        if not name:
            name = data.get("display_name")

        # Build formatted response dictionary
        return {
            "name": name,
            "lat": float(data.get("lat")),
            "lon": float(data.get("lon"))
        }

# End of file nominatim_geocoder.py
