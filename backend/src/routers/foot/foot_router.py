import asyncio
from typing import List
from routers.router import Router
from models.route import TripPattern
from models.planning_context import PlanningContext
from otp.foot import OTPFoot
from routers.router_base import RouterBase
from routing_engine.routing_context import RoutingContext
from shared.pattern_utils import PatternUtils

class FootRouter(RouterBase, Router):
    def __init__(self, context: RoutingContext):
        super().__init__(context)
        self.__otp_client = OTPFoot(self._ctx)

    async def route_group(self, context: PlanningContext) -> List[TripPattern]:
        # Create OTP routing tasks for each consecutive segment
        tasks = [
            self.__otp_client.execute(
                self._parse_coordinates(context.waypoints[k]),
                self._parse_coordinates(context.waypoints[k + 1])
            )
            for k in range(len(context.waypoints) - 1)
        ]

        results = await asyncio.gather(*tasks)

        trip_patterns = []

        # Merge segment results into a single pattern chain
        for result in results:
            # Initialize with first segment result
            if trip_patterns == []:
                trip_patterns = result
            # Append next segment legs to existing patterns
            else:
                for pattern in trip_patterns:
                    pattern.legs.extend(result[0].legs)

        # Adjust final timing of each trip pattern
        for trip_pattern in trip_patterns:
            PatternUtils.justify_time(
                trip_pattern,
                context.time_cursor,
                self._ctx.data.arrive_by
            )

        return trip_patterns
