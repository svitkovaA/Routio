from abc import ABC, abstractmethod
import asyncio
from typing import List, final
from routing_engine.routing_context import RoutingContext
from routers.router_base import RouterBase
from otp.bicycle import OTPBicycle
from otp.foot import OTPFoot
from models.planning_context import PlanningContext
from models.route import TripPattern

class BicycleRouterBase(RouterBase, ABC):
    def __init__(self, context: RoutingContext) -> None:
        super().__init__(context)
        self._otp_bicycle_client = OTPBicycle(self._ctx)
        self._otp_foot_client = OTPFoot(self._ctx)
        
    @abstractmethod
    async def route_bike_group(self, context: PlanningContext) -> List[TripPattern]:
        pass

    @final
    async def _route_bicycle_segments(self, waypoints: List[str]) -> List[TripPattern]:
        # Create OTP routing tasks for each consecutive segment
        tasks = [
            self._otp_bicycle_client.execute(
                self._parse_coordinates(waypoints[i]),
                self._parse_coordinates(waypoints[i + 1])
            )
            for i in range(len(waypoints) - 1)
        ]

        results = await asyncio.gather(*tasks)

        trip_patterns = []

        # Merge segment results into a single pattern chain
        for result in results:
            # Initialize with first segment result
            if not trip_patterns:
                trip_patterns = result
            # Append next segment legs to existing patterns
            else:
                for pattern in trip_patterns:
                    pattern.legs.extend(result[0].legs)

        return trip_patterns
