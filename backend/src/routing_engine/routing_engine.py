"""
file: routing_engine.py

Main orchestrator of the routing system, coordinates the planning pipeline.
"""

from typing import List
from gql.client import AsyncClientSession
from models.route import TripPattern, WaypointGroup
from models.route_data import LegPreferences, RouteData
from routing_engine.recursive_planner import RecursivePlanner
from routing_engine.routing_context import RoutingContext
from routing_engine.waypoint_grouper import WaypointGrouper
from shared.leg_utils import LegUtils
from shared.pattern_filtering import PatternFiltering

class RoutingEngine():
    def __init__(self, data: RouteData, session: AsyncClientSession):
        """
        Initializes the routing engine.

        Args:
            data: Route data containing waypoints and leg preferences
            session: Asynchronous GraphQL client session for API calls
        """
        self.__ctx = RoutingContext(data, session)

    async def plan_route(self) -> List[TripPattern]:
        """
        Executes the full route planning pipeline.

        Returns:
            List of TripPattern objects representing found routes
        """
        # Create waypoint groups
        groups = self.__create_groups()

        # Reverse planning direction for arrival planning
        if self.__ctx.data.arrive_by:
            groups = list(reversed(groups))
        
        # Initialize recursive planner
        recursive_planner = RecursivePlanner(self.__ctx)

        # Compute trip patterns across grouped waypoints
        trip_patterns = await recursive_planner.plan_groups(groups)

        # Postprocess legs in each trip pattern
        for pattern in trip_patterns:
            LegUtils.process_legs(pattern)

        # Filter and sort trip patterns based on the user preferences
        pattern_filtering = PatternFiltering(self.__ctx)

        return pattern_filtering.filter_and_sort(trip_patterns)

    def __create_groups(self) -> List[WaypointGroup]:
        """
        Creates waypoint groups depending on routing mode configuration.

        Returns:
            List of WaypointGroup objects for recursive planning
        """
        # Create multimodal groups based on individual leg preferences
        if self.__ctx.data.mode == "multimodal":
            return WaypointGrouper.group(
                self.__ctx.data.waypoints,
                self.__ctx.data.leg_preferences
            )
        # Create unimodal groups by applying the same mode to all legs
        else:
            return WaypointGrouper.group(
                self.__ctx.data.waypoints,
                [LegPreferences(mode=self.__ctx.data.mode, wait=0)] * len(self.__ctx.data.leg_preferences)
            )

# End of file routing_engine.py
