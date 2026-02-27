from dataclasses import dataclass
from typing import Dict, List, Tuple
from google.transit.gtfs_realtime_pb2 import FeedMessage        # type: ignore[import-untyped]
from config.datasets import GTFSRT_URL

import httpx
from service.service_base import ServiceBase

@dataclass(frozen=True)
class _GTFSRTState:
    # Maps trip_id to (latitude, longitude)
    vehicle_position_map: Dict[int, Tuple[float, float]]

class GTFSRTService(ServiceBase[_GTFSRTState]):
    def __init__(self):
        super().__init__()
        self.__client = httpx.AsyncClient(
            headers={"User-Agent": "Routio/1.0 (academic project)"},
            timeout=10
        )

    async def reload(self) -> None:
        new_state = await self.__load_data()
        self._set_state(new_state)

    def get_vehicle_positions(
        self,
        trip_ids: List[int]
    ) -> Dict[int, Dict[str, float]]:
        # Dictionary for mapping trip_id to lat, lon
        trip_id_to_position: Dict[int, Dict[str, float]] = {}

        state = self._get_state()

        for trip_id in trip_ids:
            # Retrieve vehicle position for a given trip_id
            position = state.vehicle_position_map.get(trip_id)

            if position:
                trip_id_to_position[trip_id] = {
                    "lat": position[0],
                    "lon": position[1]
                }

        return trip_id_to_position

    async def __load_data(self) -> _GTFSRTState:
        response = await self.__client.get(GTFSRT_URL)
        response.raise_for_status()
        data = response.content

        # Parse protobuf GTFS-RT message
        feed = FeedMessage()                                    # type: ignore
        feed.ParseFromString(data)                              # type: ignore
        
        # Reset and update vehicle position map
        vehicle_position_map: Dict[int, Tuple[float, float]] = {}

        for entity in feed.entity:                              # type: ignore
            # Process only vehicle position entities
            if entity.HasField("vehicle"):                      # type: ignore
                v = entity.vehicle                              # type: ignore

                # Skip entities without a valid trip ID
                if not (v.HasField("trip") and v.trip.trip_id): # type: ignore
                    continue
                
                trip_id = int(v.trip.trip_id)                   # type: ignore
                
                # Skip entities without valid position data
                if not (v.HasField("position") and v.position.latitude and v.position.longitude):   # type: ignore
                    continue
                
                # Store current vehicle position for the trip
                vehicle_position_map[trip_id] = (v.position.latitude, v.position.longitude)         # type: ignore
        
        return _GTFSRTState(vehicle_position_map=vehicle_position_map)
