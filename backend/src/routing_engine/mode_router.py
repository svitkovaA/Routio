"""
file: mode_router.py

Provides a routing dispatcher that delegates routing logic to concrete
transport mode routers.
"""

from datetime import datetime
from typing import Dict, List
from routers.router import Router
from routers.bicycles.bicycle_router import BicycleRouter
from models.planning_context import PlanningContext
from models.route import RoutingMode, TripPattern, WaypointGroup
from routing_engine.routing_context import RoutingContext
from routers.foot.foot_router import FootRouter
from routers.bicycle_public.bicycle_public_router import BicyclePublicRouter
from routers.public_transport.public_transport_router import PublicTransportRouter
from routers.public_bicycle.public_bicycle_router import PublicBicycleRouter

class ModeRouter():
    """
    Routing dispatcher responsible for delegating route computation.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes mode router with available transport routers.

        Args:
            context: Shared RoutingContext used by all mode routers
        """
        self.__ctx = context

        # Initialize available transport routers mapped to routing modes
        self.__routers: Dict[RoutingMode, Router] = {
            "foot": FootRouter(self.__ctx),
            "bicycle": BicycleRouter(self.__ctx),
            "bicycle_public": BicyclePublicRouter(self.__ctx),
            "walk_transit": PublicTransportRouter(self.__ctx),
            "public_bicycle": PublicBicycleRouter(self.__ctx)
        }
    
    async def route_group(
        self,
        group: WaypointGroup,
        time_cursor: datetime
    ) -> List[TripPattern]:
        """
        Routes a single waypoint group using the appropriate transport router.

        Args:
            group: Waypoint group to be routed
            time_cursor: Current temporal reference for routing

        Returns:
            List of TripPattern objects generated for the given group
        """
        # Return empty result if routing mode is not supported
        if group.mode not in self.__routers:
            return []

        # Delegate routing to the corresponding transport mode router
        else:
            return await self.__routers[group.mode].route_group(PlanningContext(
                waypoints=group.waypoints,
                time_cursor=time_cursor
            ))

# End of file mode_grouper.py
