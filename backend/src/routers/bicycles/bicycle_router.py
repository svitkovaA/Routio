from typing import List, final
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
    def __init__(self, context: RoutingContext):
        super().__init__(context)
        self._otp_bicycle_client = OTPBicycle(self._ctx)
        self._otp_foot_client = OTPFoot(self._ctx)
        self.__router: BicycleRouterBase = (
            OwnBicycleRouter(self._ctx)
            if self._ctx.data.use_own_bike
            else SharedBicycleRouter(self._ctx)
        )

    @final
    async def route_group(self, context: PlanningContext) -> List[TripPattern]:
        return await self.__router.route_bike_group(context)
    
