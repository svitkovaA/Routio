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
    # Maps trip_id to (latitude, longitude, delay in minutes)
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

            # Store computed delay
            trip_realtime_data[trip_id] = (
                (lat, lon),
                int(delay_minutes),
                best_index
            )
    
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
        # Initialize minimum score
        min_score = float("inf")

        # Index of the best matching segment
        best_index = 0

        # Iterate through consecutive stop pairs
        for i in range(len(trip_stops) - 1):
            # Extract stop identifiers forming the segment
            stop_a_id = trip_stops[i][0]
            stop_b_id = trip_stops[i + 1][0]

            # Extract stop identifiers forming the segment
            coords_a = self.__gtfs_service.get_stop_coordinates(dataset_name, stop_a_id)
            coords_b = self.__gtfs_service.get_stop_coordinates(dataset_name, stop_b_id)

            # Skip if coordinates are missing
            if not coords_a or not coords_b:
                continue

            lat_a, lon_a = coords_a
            lat_b, lon_b = coords_b

            # Compute distance from vehicle to first stop of segment
            dist_a = GeoMath.haversine_distance_km(position_lat, position_lon, lat_a, lon_a)

            # Compute distance from vehicle to second stop of segment
            dist_b = GeoMath.haversine_distance_km(position_lat, position_lon, lat_b, lon_b)

            # Use sum of distances as a segment proximity score
            score = dist_a + dist_b

            # Updates best index if current score is better
            if score < min_score:
                min_score = score
                best_index = i

        return best_index

# End of file gtfs_rt_service.py
