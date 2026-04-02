"""
file: gtfs_rt_service.py

This file implements an asynchronous GTFS-RT service. It handles downloading
and processing realtime GTFS-RT dataset.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
from typing import Dict, List, Tuple
import pandas as pd
from google.transit.gtfs_realtime_pb2 import FeedMessage    # type: ignore[import-untyped]
from models.route import TZ
from models.vehicle_realtime_request_data import VehicleRealtimeRequestData
from shared.geo_math import GeoMath
from config.datasets import GTFS_DATASETS, GTFS_DATASET
from service.gtfs_service import GTFSService
from service.service_base import ServiceBase

TripRealtimeCache = Dict[str, Tuple[Tuple[float, float], int | None, int | None]]

@dataclass(frozen=True)
class _GTFSRTState:
    """
    Processed GTFS-RT data representation.
    """
    # Maps trip_id to (latitude, longitude, delay in minutes and closest stop id)
    trip_realtime_data: TripRealtimeCache

class GTFSRTService(ServiceBase[Dict[str, _GTFSRTState]]):
    """
    Service responsible for retrieving and processing GTFS-Realtime vehicle data.
    """
    def __init__(self):
        super().__init__()

        # Asynchronous HTTP client for GTFS-RT requests
        self.__client = httpx.AsyncClient(
            headers={"User-Agent": "Routio/1.0 (academic project)"},
            timeout=10
        )

        # Reference to static GTFS service
        self.__gtfs_service = GTFSService.get_instance()

    async def reload(self) -> None:
        """
        Reloads GTFS-RT data and builds internal state.
        """
        datasets_with_rt = [
            dataset for dataset in GTFS_DATASETS if dataset["realtime"] is not None
        ]

        states = await asyncio.gather(*[
            self.__build_realtime_state(dataset)
            for dataset in datasets_with_rt
        ])

        new_state = {
            dataset["name"]: state
            for state, dataset in zip(states, datasets_with_rt)
        }
        self._set_state(new_state)

    def get_vehicle_realtime_data(
        self,
        real_time_data: List[VehicleRealtimeRequestData]
    ) -> Dict[str, Dict[str, float]]:
        """
        Retrieves realtime vehicle positions for given trip identifiers and
        provides computed delay information.

        Args:
            real_time_data: List of real time data
        
        Returns:
            Mapping trip_id to latitude and longitude coordinates and delay
        """

        # Maps trip_id to (latitude, longitude)
        trip_id_to_position: Dict[str, Dict[str, float]] = {}

        state = self._get_state()

        # Reference time
        now = datetime.now(TZ)

        for data in real_time_data:
            # Determines window
            window_start = data.start_time - timedelta(minutes=10)
            window_end = data.start_time + timedelta(hours=12)

            # Skip data which are not in a window
            if window_start > now or now > window_end:
                continue

            dataset_name = self.__gtfs_service.get_dataset_name_by_agency(data.agency_name)
            if dataset_name is None or dataset_name not in state:
                continue

            # Retrieve cached vehicle position for a given trip_id
            position = state[dataset_name].trip_realtime_data.get(data.trip_id)

            if position:
                # Store latitude and longitude
                trip_id_to_position[data.trip_id] = {
                    "lat": position[0][0],
                    "lon": position[0][1]
                }

                # Include delay if available
                if position[1] is not None:
                    trip_id_to_position[data.trip_id]["delay"] = position[1]

                # Include stop position if available
                if position[2] is not None:
                    trip_id_to_position[data.trip_id]["stopIndex"] = position[2]

        return trip_id_to_position

    async def __build_realtime_state(self, dataset: GTFS_DATASET) -> _GTFSRTState:
        """
        Downloads and processes the GTFS-Realtime feed.

        Returns:
            Initialized _GTFSRTState
        """
        if dataset["realtime"] is None:
            raise ValueError("Invalid GTFSRT url link")

        # Download GTFS-RT feed
        response = await self.__client.get(dataset["realtime"])
        response.raise_for_status()
        data = response.content

        # Parse protobuf message
        feed = FeedMessage()                                    # type: ignore
        feed.ParseFromString(data)                              # type: ignore
        
        # Initialize vehicle position cache
        trip_realtime_data: TripRealtimeCache = {}

        for entity in feed.entity:                              # type: ignore
            # Process only vehicle position entities
            if entity.HasField("vehicle"):                      # type: ignore
                v = entity.vehicle                              # type: ignore

                # Skip entities without trip_id
                if not (v.HasField("trip") and v.trip.trip_id): # type: ignore
                    continue
                
                trip_id = v.trip.trip_id                        # type: ignore
                
                # Skip entities without position data
                if not (v.HasField("position") and v.position.latitude and v.position.longitude):   # type: ignore
                    continue
                
                # Store current vehicle position for the trip with a timestamp
                trip_realtime_data[trip_id] = (
                    (v.position.latitude, v.position.longitude),    # type: ignore
                    int(v.timestamp) if v.timestamp else None,      # type: ignore
                    None
                )

        # Compute delays for each vehicle
        self.__compute_interpolated_trip_delays(dataset["name"], trip_realtime_data)
        
        return _GTFSRTState(trip_realtime_data=trip_realtime_data)

    def __compute_interpolated_trip_delays(
        self,
        dataset_name: str,
        trip_realtime_data: TripRealtimeCache
    ) -> None:
        """
        Computes interpolated delay values for each trip in the realtime cache.

        Args:
            dataset_name: GTFS dataset name
            trip_realtime_data: Mapping trip_id to ((latitude, longitude), unix_timestamp)
        """        
        # Iterate through all vehicle positions
        for trip_id, ((lat, lon), unix_timestamp, _) in trip_realtime_data.items():

            # Set delay to None by default
            trip_realtime_data[trip_id] = ((lat, lon), None, None)

            # Skip if timestamp is missing
            if not unix_timestamp:
                continue

            # Get ordered stops for the trip
            trip_stops = self.__gtfs_service.get_trip_stops(dataset_name, trip_id)

            # Skip if stop data are missing
            if not trip_stops or len(trip_stops) < 2:
                continue

            # Find closest stop segment
            best_index = self.__find_closest_segment_index(dataset_name, trip_stops, lat, lon)

            if best_index >= len(trip_stops) - 1:
                continue

            # Get adjacent stops and their scheduled times
            stop_a, time_a_str, _ = trip_stops[best_index]
            stop_b, time_b_str, _ = trip_stops[best_index + 1]

            # Get stop coordinates
            stop_a_coordinates = self.__gtfs_service.get_stop_coordinates(dataset_name, stop_a)
            stop_b_coordinates = self.__gtfs_service.get_stop_coordinates(dataset_name, stop_b)

            # Skip if stop coordinates are missing
            if not stop_a_coordinates or not stop_b_coordinates:
                continue

            lat_a, lon_a = stop_a_coordinates
            lat_b, lon_b = stop_b_coordinates

            # Compute distance between stops in meters
            distance_between_stops = GeoMath.haversine_distance_km(
                lat_a,
                lon_a,
                lat_b,
                lon_b
            ) * 1000

            # Compute distance from stop a to vehicle
            distance_vehicle = GeoMath.haversine_distance_km(
                lat_a,
                lon_a,
                lat,
                lon
            ) * 1000

            # Compute interpolation ratio within segment
            ratio = (
                0 if distance_between_stops == 0 
                else min(max(distance_vehicle / distance_between_stops, 0), 1)
            )

            # Convert GTFS times to timedelta
            td_a = pd.to_timedelta(time_a_str)
            td_b = pd.to_timedelta(time_b_str)

            # Convert vehicle timestamp to datetime
            vehicle_time = datetime.fromtimestamp(unix_timestamp)

            # Build scheduled datetimes for stops
            scheduled_a = datetime.combine(vehicle_time.date(), datetime.min.time()) + td_a
            scheduled_b = datetime.combine(vehicle_time.date(), datetime.min.time()) + td_b

            # Interpolate scheduled time at vehicle position
            scheduled_time = scheduled_a + ratio * (scheduled_b - scheduled_a)

            # Compute delay in minutes
            delay_minutes = (vehicle_time - scheduled_time).total_seconds() / 60

            # Threshold to detect if vehicle is at stop A
            STOP_THRESHOLD_METERS = 15

            # Distance from vehicle to stop A
            distance_to_a = GeoMath.haversine_distance_km(
                lat, lon,
                lat_a, lon_a
            ) * 1000

            # Determine which stop index should be reported
            if distance_to_a <= STOP_THRESHOLD_METERS:
                target_index = best_index
            else:
                target_index = best_index + 1

            # Store computed delay and stop index
            trip_realtime_data[trip_id] = (
                (lat, lon),
                int(delay_minutes),
                target_index
            )

    @staticmethod
    def vector(
        a_lat: float,
        a_lon: float,
        b_lat: float,
        b_lon: float
    ) -> Tuple[float, float]:
        """
        Computes vector from point A to point B.
        """
        return (b_lat - a_lat, b_lon - a_lon)
    
    @staticmethod
    def dot(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """
        Computes dot product of two vectors.
        """
        return a[0] * b[0] + a[1] * b[1]
    
    def __find_closest_segment_index(
        self,
        dataset_name: str,
        trip_stops: List[Tuple[str, str, int]],
        position_lat: float,
        position_lon: float
    ) -> int:
        """
        Finds the index of the stop segment closest to the given vehicle position.

        Args:
            dataset_name: GTFS dataset name
            trip_stops: All stops on trip
            position_lat: Current vehicle position latitude
            position_lon: Current vehicle position longitude
        
        Returns:
            Best index i representing the first stop for interpolation
        """

        # Initialize best matching segment
        best_index = 0
        best_distance = float("inf")

        # Find closest stop by distance
        for index, trip_stop in enumerate(trip_stops):
            coordinates = self.__gtfs_service.get_stop_coordinates(dataset_name, trip_stop[0])

            if not coordinates:
                continue

            distance = GeoMath.haversine_distance_km(position_lat, position_lon, *coordinates)

            if distance < best_distance:
                best_distance = distance
                best_index = index

        # If closest stop is first or last, return directly
        if best_index == 0 or best_index == len(trip_stops) - 1:
            return best_index
        
        # Get coordinates for direction check
        best_index_coords = self.__gtfs_service.get_stop_coordinates(dataset_name, trip_stops[best_index][0])
        next_coords = self.__gtfs_service.get_stop_coordinates(dataset_name, trip_stops[best_index + 1][0])

        if best_index_coords is None or next_coords is None:
            return best_index

        # Vector from current stop to next stop
        vector_best_next = self.vector(*best_index_coords, *next_coords)

        # Vector from current stop to vehicle
        vector_best_vehicle = self.vector(*best_index_coords, position_lat, position_lon)

        # Dot product determines if vehicle is ahead or behind the stop
        dot_next = self.dot(vector_best_next, vector_best_vehicle)

        # If vehicle is in direction of next stop, use current segment
        if dot_next > 0:
            return best_index
        # Otherwise, vehicle is before current stop, use previous segment
        else:
            return best_index - 1

# End of file gtfs_rt_service.py
