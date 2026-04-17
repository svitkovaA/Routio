"""
file: gbfs_service.py

Service for retrieving and caching GBFS station capacity data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple
import httpx
from models.route import TZ
from config.datasets import GBFS_URLS
from service.service_base import ServiceBase

@dataclass(frozen=True)
class _GBFSState:
    """
    Internal state of the GBFS service.
    """
    # Set of station ids
    station_ids: Set[str]

    # Maps station id to (capacity, latitude, longitude, name, current number of available bicycles)
    station_info: Dict[str, Tuple[int | None, float, float, str, int]]

    # State capture timestamp
    timestamp: int

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

    async def _shutdown(self) -> None:
        """
        Gracefully releases service resources.
        """
        await self.__client.aclose()

    async def reload(self) -> None:
        """
        Reloads GBFS data and replaces the internal cached state.
        """
        print("Loading GBFS cache")

        new_state = await self.__load_state()
        self._set_state(new_state)

    async def __load_state(self) -> _GBFSState:
        """
        Downloads GBFS feeds and extracts information.

        Returns:
            Initialized internal _GBFSState
        """
        # Set of station ids
        station_ids: Set[str] = set()

        # Maps station id to (capacity, latitude, longitude, name, current number of available bicycles)
        station_info: Dict[str, Tuple[int | None, float, float, str, int]] = {}

        # Iterate over all configured GBFS URLs
        for url in GBFS_URLS:
            try:
                response = await self.__client.get(url)
                response.raise_for_status()
                response_data = response.json()

                # Extract english url feeds
                feeds: List[Dict[str, str]] = response_data["data"]["en"]["feeds"]

                station_information_url: str | None = None
                station_status_url: str | None = None
                for feed in feeds:
                    if feed["name"] == "station_information":
                        station_information_url = feed["url"]
                    elif feed["name"] == "station_status":
                        station_status_url = feed["url"]

                if station_information_url is None or station_status_url is None:
                    print(f"WARNING: Invalid gbfs url: {url}")
                    continue

                station_information_response = await self.__client.get(station_information_url)
                station_information_response.raise_for_status()
                station_information_data: Dict[str, Any] = station_information_response.json()

                # Extract stations array from GBFS structure
                stations: List[Dict[str, Any]] = station_information_data.get("data", {}).get("stations", [])
                
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
                        station["name"],
                        -1
                    )

                station_status_response = await self.__client.get(station_status_url)
                station_status_response.raise_for_status()
                station_status_data: Dict[str, Any] = station_status_response.json()

                # Extract stations array from GBFS structure
                stations = station_status_data["data"]["stations"]

                # Process each station entry
                for station in stations:
                    # Retrieve station id
                    station_id = station["station_id"]

                    if station_id not in station_info:
                        continue

                    # Update record with currently available bicycles
                    record = station_info[station_id]
                    station_info[station_id] = (
                        record[0],
                        record[1],
                        record[2],
                        record[3],
                        station.get("num_bikes_available", -1)
                    )

            except Exception as e:
                print(f"GBFS error for {url}: {e}")
                continue

        return _GBFSState(
            station_ids=station_ids,
            station_info=station_info,
            timestamp=int(datetime.now(tz=TZ).timestamp()) * 1000
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

    def get_bicycle_rows(self) -> List[Tuple[int, int, int]]:
        """
        Returns processed bicycle availability records.

        Returns:
            List of tuples containing station id, timestamp, and number of available bikes
        """
        state = self._get_state()
        return [
            (int(station_id), state.timestamp, item[4])
            for station_id, item in state.station_info.items()
            if item[4] != -1
        ]

# End of file gbfs_service.py
