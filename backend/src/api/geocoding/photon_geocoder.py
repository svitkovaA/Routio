from typing import List
from shared.geo_math import GeoMath
from api.geocoding.geocoder_base import GeocoderBase
from models.suggestions import Suggestion
from config.external import PHOTON_URL

class PhotonGeocoder(GeocoderBase):
    def __init__(self):
        super().__init__(PHOTON_URL)

    async def geocode(
        self,
        query: str,
        limit: int
    ) -> List[Suggestion]:
        bbox = "15.7,48.8,16.7,49.3"

        data = await self._get({
            "q": query,
            "limit": limit * 3,
            "lang": "en",
            "bbox": bbox
        })

        suggestions: List[Suggestion] = []

        for feature in data.get("features", []):
            lon, lat = feature["geometry"]["coordinates"]
            props = feature["properties"]

            suggestions.append(Suggestion(
                name=props.get("name"),
                type=props.get("type"),
                country=props.get("country"),
                city=props.get("city"),
                street=props.get("street"),
                lat=lat,
                lon=lon
            ))

        return self.__merge_close_results(suggestions)[:limit]
    
    @staticmethod
    def __merge_close_results(
        results: List[Suggestion],
        max_distance: float=20
    ) -> List[Suggestion]:
        """
        Merge close and duplicate search results

        Args:
            results: List of search results containing location information
            max_distance: Maximal distance in meters for merging close results

        Returns:
            New list of merged results
        """
        merged: List[Suggestion] = []
        
        for candidate in results:
            duplicate = False
            for existing in merged:
                same_name = (
                    candidate.name == existing.name and
                    candidate.type == existing.type and
                    candidate.country == existing.country and
                    candidate.city == existing.city and
                    (
                        candidate.street == existing.street or
                        candidate.street is None or
                        existing.street is None
                    )
                )

                too_close = (
                    GeoMath.haversine_distance_km(
                        candidate.lat,
                        candidate.lon,
                        existing.lat,
                        existing.lon
                    ) * 1000 < max_distance
                )

                if same_name or too_close:
                    duplicate = True
                    break

            if not duplicate:
                merged.append(candidate)

        return merged
