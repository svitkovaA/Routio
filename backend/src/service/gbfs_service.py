from dataclasses import dataclass
from typing import Dict
import httpx
from config.datasets import STATION_INFORMATION_URLS
from service.service_base import ServiceBase

@dataclass(frozen=True)
class _GBFSState:
    # Maps station_id to capacity
    capacities: Dict[str, int]

class GBFSService(ServiceBase[_GBFSState]):
    def __init__(self):
        super().__init__()
        self.__client = httpx.AsyncClient(
            headers={"User-Agent": "Routio/1.0 (academic project)"},
            timeout=10
        )

    async def reload(self) -> None:
        print("Loading GBFS cache")
        new_state = await self.__fetch_data()
        self._set_state(new_state)

    async def __fetch_data(self) -> _GBFSState:
        capacities: Dict[str, int] = {}

        # Get station information
        for url in STATION_INFORMATION_URLS:
            try:
                response = await self.__client.get(url)
                response_data = response.json()
                stations = response_data.get("data", {}).get("stations", [])
                
                # Map station_id to capacity if provided
                for station in stations:
                    capacity = station.get("capacity")
                    if capacity is not None:
                        capacities[station["station_id"]] = capacity
            except Exception:
                continue

        return _GBFSState(capacities=capacities)
    
    def get_capacity(self, station_id: str) -> int | None:
        state = self._get_state()
        return state.capacities.get(station_id)
