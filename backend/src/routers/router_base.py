"""
file: router_base.py

Provides a shared base implementation for concrete router classes.
"""

from abc import ABC
from datetime import timedelta
from typing import List, Tuple, final
from models.route import TripPattern
from shared.geo_math import GeoMath
from routing_engine.routing_context import RoutingContext

class RouterBase(ABC):
    """
    Base class for router implementations.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes router with shared routing context.
        
        Args:
            context: RoutingContext containing global route configuration
        """
        self._ctx = context

    @final
    @staticmethod
    def _parse_coordinates(value: str) -> Tuple[float, float]:
        """
        Parses a coordinate string into latitude and longitude.
        
        Args:
            value: Coordinate string in format lat,lon
            
        Returns:
            Tuple (latitude, longitude) as floats
        """
        lat, lon = value.split(",")

        return float(lat), float(lon)
    
    def _estimate_public_time_duration(self, waypoints: List[str]) -> timedelta:
        """
        Estimate travel duration for public transport between waypoints.

        Args:
            waypoints: List of waypoint coordinates

        Returns:
            Estimated travel time
        """
        total_distance = 0.0

        # Sum adjusted distances between consecutive waypoints
        for index in range(len(waypoints) - 1):
            total_distance += GeoMath.haversine_distance_km(
                *self._parse_coordinates(waypoints[index]),
                *self._parse_coordinates(waypoints[index + 1])
            ) * 1.4

        # Estimate average speed based on total distance
        estimated_speed = self.__estimate_speed(total_distance)

        # Compute travel time
        estimated_time = total_distance / estimated_speed

        return timedelta(hours=estimated_time)

    @staticmethod
    def __estimate_speed(distance_km: float) -> float:
        """
        Estimate average transport speed based on travel distance.

        Args:
            distance_km: Total travel distance in kilometers

        Returns:
            Estimated speed in km/h
        """
        return min(50, 12 + 0.7 * distance_km)

    @staticmethod
    def _compute_bike_distance(pattern: TripPattern) -> float:
        """
        Computes total bicycle distance within a trip pattern.

        Args:
            pattern: TripPattern containing bike legs

        Returns:
            Sum of distances of all bike legs
        """
        return sum(
            leg.distance
            for leg in pattern.legs
            if leg.mode == "bicycle"
        )

# End of file router_base.py
