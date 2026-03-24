"""
file: gbfs_service.py

Service for retrieving and caching GBFS station capacity data.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
import httpx
from config.datasets import STATION_INFORMATION_URLS
from service.service_base import ServiceBase

@dataclass(frozen=True)
class _GBFSState:
    """
    Internal state of the GBFS service.
    """
    # Set of station ids
    station_ids: Set[str]

    # Maps station id to (capacity, latitude, longitude, name)
    station_info: Dict[str, Tuple[int | None, float, float, str]]

class GBFSService(ServiceBase[_GBFSState]):
    """
    Service responsible for loading and caching GBFS station information.
    """
    def __init__(self):
        super().__init__()

        # Asynchronous HTTP client for GBFS requests
        self.__client = httpx.AsyncClient(
            headers={"User-Agent": "Routio/1.0 (academic project)"},
            timeout=10
        )

    async def reload(self) -> None:
        """
        Reloads GBFS data and replaces the internal cached state.
        """
        print("Loading GBFS cache")

        new_state = await self.__fetch_data()
        self._set_state(new_state)

    async def __fetch_data(self) -> _GBFSState:
        """
        Downloads GBFS station information feeds and extracts capacities.

        Returns:
            Initialized internal _GBFSState
        """
        # Set of station ids
        station_ids: Set[str] = set()

        # Maps station id to (capacity, latitude, longitude, name)
        station_info: Dict[str, Tuple[int | None, float, float, str]] = {}

        # Iterate over all configured GBFS station information URLs
        for url in STATION_INFORMATION_URLS:
            try:
                response = await self.__client.get(url)
                response_data = response.json()

                # Extract stations array from GBFS structure
                stations = response_data.get("data", {}).get("stations", [])
                
                # Process each station entry
                for station in stations:
                    # Retrieve capacity value if present
                    capacity = station.get("capacity")

                    # Retrieve station ids
                    station_ids.add(station["station_id"])
                    
                    # Store station latitude and longitude
                    station_info[station["station_id"]] = (
                        capacity,
                        station["lat"],
                        station["lon"],
                        station["name"]
                    )

            except Exception:
                continue

        return _GBFSState(
            station_ids=station_ids,
            station_info=station_info
        )
    
    def get_capacity(self, station_id: str) -> int | None:
        """
        Retrieves the capacity of a specific GBFS station.

        Args:
            station_id: Identifier of the station

        Returns:
            Station capacity if available
        """
        # Retrieve capacity for a specific station_id
        state = self._get_state()
        station = state.station_info.get(station_id)

        # Return capacity if available
        if station is not None:
            return station[0]
        
        return None

    def valid_station_id(self, station_id: str) -> bool:
        """
        Checks whether a station id exists in the dataset.

        Args:
            station_id: Station identifier to validate

        Returns:
            True if the station id exists, false otherwise
        """
        state = self._get_state()

        return station_id in state.station_ids
    
    def get_station_info(self) -> List[Dict[str, str | float]]:
        """
        Get station information including id and coordinates.

        Returns:
            List of dicts (station id, latitude, longitude, name)
        """
        state = self._get_state()
        return [
            {
                "id": key,
                "lat": item[1],
                "lon": item[2],
                "name": item[3]
            }
            for key, item in state.station_info.items()
        ]

# End of file gbfs_service.py
