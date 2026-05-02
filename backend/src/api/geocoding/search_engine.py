"""
file: search_engine.py

Implementation of search engine using Photon API and GTFS stops.
"""

from dataclasses import dataclass
from typing import List, Literal
from api.geocoding.photon_geocoder import PhotonGeocoder
from shared.geo_math import GeoMath
from service.gtfs_service import GTFSService

@dataclass
class SearchResult:
    """
    Representation of search result.
    """
    name: str                           # Display name of the result
    lat: float                          # Latitude coordinate
    lon: float                          # Longitude coordinate
    source: Literal["stop", "photon"]   # Origin of result
    isTrain: bool = False               # Whether result represents train stop
    isBus: bool = False                 # Whether result represents bus/tram stop
    type: str | None = None             # Photon-specific type
    
class SearchEngine:
    """
    Combines GTFS stop search and Photon geocoding.
    """
    def __init__(self):
        """
        Initializes search engine with required services.
        """
        self.__photon = PhotonGeocoder()
        self.__gtfs_service = GTFSService.get_instance()
        
    async def search(self, query: str, limit: int) -> List[SearchResult]:
        """
        Performs combined search over GTFS stops and Photon API.

        Args:
            query: User input query string
            limit: Maximum number of results to return

        Returns:
            List of sorted and deduplicated search results
        """
        # Retrieve matching GTFS stops
        stops = self.__gtfs_service.search_stops(query, limit)
        
        # Retrieve Photon geocoder results
        photon_results = await self.__photon.geocode(query, limit)
        
        results: List[SearchResult] = []
        
        # Convert GTFS stops to unified format
        for s in stops:
            results.append((SearchResult(
                name=s.name,
                lat=s.lat,
                lon=s.lon,
                source="stop",
                isTrain=s.is_train,
                isBus=s.is_bus
            )))
         
        # Convert Photon results to unified format   
        for r in photon_results:
            parts: List[str | None] = [r.name, r.street, r.city]
            # Limit name to at most two components to reduce verbosity
            name = ", ".join([part for part in parts if part][:2])
            results.append(SearchResult(
                name=name,
                lat=r.lat,
                lon=r.lon,
                source="photon",
                type=r.type
            ))
            
        # Score all results
        scored = [(self.__score(query, result), result) for result in results]
        
        # Sort by score
        scored.sort(key=lambda x: x[0])
        results_sorted = [r for _, r in scored]

        # Remove duplicates
        results_dedup = self.__deduplicate(results_sorted)

        return results_dedup[:limit]
            
    def __score(self, query: str, result: SearchResult) -> int:
        """
        Computes ranking score for a single result.
        Lower score means higher relevance.

        Args:
            query: User query
            result: Candidate search result

        Returns:
            Integer score
        """
        q = self.__gtfs_service.normalize_query(query)
        name = self.__gtfs_service.normalize_query(result.name)
        
        score = 0
        
        # Match quality scoring
        if name == q:
            score -= 100
        elif name.startswith(q):
            score -= 50
        elif q in name:
            score -= 20
            
        # Prefer GTFS stops slightly
        if result.source == "stop":
            score -= 20
        
        # Adjust Photon results based on type
        if result.source == "photon":
            if result.type == "street":
                score -= 10
            elif result.type != "house":
                score += 10
                
        return score
    
    def __deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Removes duplicate results based on spatial proximity and name similarity.

        Args:
            results: Ranked list of results

        Returns:
            Deduplicated list preserving ranking priority
        """
        unique: List[SearchResult] = []

        for candidate in results:
            replaced = False

            for i, existing in enumerate(unique):
                # Check name similarity
                name_similar = self.__similar_names(candidate.name, existing.name)

                # Compute spatial distance
                dist = GeoMath.haversine_distance_km(
                    candidate.lat,
                    candidate.lon,
                    existing.lat,
                    existing.lon
                ) * 1000

                close = dist < 200

                if name_similar and close:
                    # Prefer GTFS stop over Photon result
                    if candidate.source == "stop" and existing.source == "photon":
                        unique[i] = candidate
                        replaced = True
                        break

                    # If existing is already stop, ignore candidate
                    if existing.source == "stop":
                        replaced = True
                        break

            if not replaced:
                unique.append(candidate)

        return unique
    
    def __similar_names(self, a: str, b: str) -> bool:
        """
        Determines whether two names are similar based on token overlap.

        Args:
            a: First name
            b: Second name

        Returns:
            True if names share significant portion of tokens
        """
        na = self.__gtfs_service.normalize_query(a)
        nb = self.__gtfs_service.normalize_query(b)
        ta = set(na.split())
        tb = set(nb.split())
        common = ta & tb
        
        # Consider similar if at least half of tokens overlap
        return len(common) >= min(len(ta), len(tb)) / 2

# End of file search_engine.py
