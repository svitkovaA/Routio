"""
file: photon_geocoder.py

Implementation of geocoding service using the Photon API.
"""

from typing import List
from shared.geo_math import GeoMath
from api.geocoding.geocoder_base import GeocoderBase
from models.suggestions import Suggestion
from config.external import PHOTON_URL

class PhotonGeocoder(GeocoderBase):
    """
    Geocoder implementation using the Photon API service.
    """
    def __init__(self):
        """
        Initializes Photon geocoder with configured base URL.
        """
        super().__init__(PHOTON_URL)

    async def geocode(
        self,
        query: str,
        limit: int
    ) -> List[Suggestion]:
        """
        Performs geocoding request and returns merged search suggestions.

        Args:
            query: User search input string
            limit: Maximum number of results to return

        Returns:
            List of Suggestion objects limited to requested count
        """
        # Bounding box limiting search area
        bbox = "15.5,48.6,17.6,49.65"

        # Photon API call
        data = await self._get({
            "q": query,
            "limit": limit * 3,
            "lang": "en",
            "bbox": bbox
        })

        # Parsed suggestions list
        suggestions: List[Suggestion] = []

        # Parse features returned by Photon
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

        # Merge duplicates and limit final results
        return self.__merge_close_results(suggestions)[:limit]
    
    @staticmethod
    def __merge_close_results(
        results: List[Suggestion],
        max_distance: float=20
    ) -> List[Suggestion]:
        """
        Merge spatially close or duplicate search results.

        Args:
            results: List of suggestions
            max_distance: Maximal distance in meters for merging close results

        Returns:
            New list of merged results
        """
        # Final merged results
        merged: List[Suggestion] = []
        
        for candidate in results:
            duplicate = False
            for existing in merged:
                # Check if information matches
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

                # Check if spatially too close
                too_close = (
                    GeoMath.haversine_distance_km(
                        candidate.lat,
                        candidate.lon,
                        existing.lat,
                        existing.lon
                    ) * 1000 < max_distance
                )

                # Mark as duplicate if either condition matches
                if same_name or too_close:
                    duplicate = True
                    break

            # Append only unique candidates
            if not duplicate:
                merged.append(candidate)

        return merged

# End of file photon_geocoder.py
