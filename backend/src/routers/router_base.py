"""
file: router_base.py

Provides a shared base implementation for concrete router classes.
"""

from abc import ABC
from typing import Tuple, final
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

# End of file router_base.py
