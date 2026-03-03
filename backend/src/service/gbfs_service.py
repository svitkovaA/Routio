"""
file: gbfs_service.py

Service for retrieving and caching GBFS station capacity data.
"""

from dataclasses import dataclass
from typing import Dict
import httpx
from config.datasets import STATION_INFORMATION_URLS
from service.service_base import ServiceBase

@dataclass(frozen=True)
class _GBFSState:
    """
    Internal state of the GBFS service
    """
    # Maps station_id to capacity
    capacities: Dict[str, int]

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
        # Maps statin_id to capacity
        capacities: Dict[str, int] = {}

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

                    # Store capacity if available
                    if capacity is not None:
                        capacities[station["station_id"]] = capacity

            except Exception:
                continue

        return _GBFSState(capacities=capacities)
    
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
        return state.capacities.get(station_id)

# End of file gbfs_service.py
