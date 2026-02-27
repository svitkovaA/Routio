from abc import ABC
from typing import Tuple, final
from routing_engine.routing_context import RoutingContext

class RouterBase(ABC):
    def __init__(self, context: RoutingContext):
        self._ctx = context

    @final
    @staticmethod
    def _parse_coordinates(value: str) -> Tuple[float, float]:
        lat, lon = value.split(",")
        return float(lat), float(lon)
