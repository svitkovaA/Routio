from api.geocoding.geocoder_base import GeocoderBase
from config.external import NOMINATIM_URL
from typing import Dict, Any

class NominatimGeocoder(GeocoderBase):
    def __init__(self):
        super().__init__(NOMINATIM_URL)

    async def reverse(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:
        data = await self._get({
            "format": "json",
            "lat": lat,
            "lon": lon,
            "addressdetails": 1,
            "zoom": 18
        })

        address = data.get("address", {})

        return {
            "name": data.get("display_name"),
            "city": address.get("city")
                    or address.get("town")
                    or address.get("village"),
            "street": address.get("road", "") + (
                (" " + address.get("house_number"))
                if not address.get("road") and address.get("house_number")
                else ""
            ),
            "lat": float(data.get("lat")),
            "lon": float(data.get("lon"))
        }
