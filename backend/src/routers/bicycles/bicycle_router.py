"""
file: bicycle_router.py

This file provides a unified bicycle router that delegates routing to either
own bicycle or shared bicycle implementations based on user configuration.
"""

from typing import List
from routers.router import Router
from otp.bicycle import OTPBicycle
from otp.foot import OTPFoot
from models.planning_context import PlanningContext
from models.route import TripPattern
from routers.bicycles.bicycle_router_base import BicycleRouterBase
from routers.bicycles.own_bicycle.own_bicycle_router import OwnBicycleRouter
from routers.bicycles.shared_bicycle.shared_bicycle_router import SharedBicycleRouter
from routing_engine.routing_context import RoutingContext
from routers.router_base import RouterBase

class BicycleRouter(RouterBase, Router):
    """
    Bicycle routing entry point.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes the bicycle router.

        Args:
            context: Global routing context containing configuration
        """
        # Initialize base router context
        super().__init__(context)

        # OTP client for bicycle routing requests
        self._otp_bicycle_client = OTPBicycle(self._ctx)

        # OTP client for walking segments
        self._otp_foot_client = OTPFoot(self._ctx)

        # Select concrete bicycle router
        self.__router: BicycleRouterBase = (
            OwnBicycleRouter(self._ctx)
            if self._ctx.data.use_own_bike
            else SharedBicycleRouter(self._ctx)
        )

    async def route_group(self, context: PlanningContext) -> List[TripPattern]:
        """
        Routes a group using the selected bicycle router.

        Args:
            context: Planning context containing routing parameters

        Returns:
            List of computed trip patterns
        """
        return await self.__router.route_bike_group(context)
    
# End of file bicycle_router.py
