"""
file: recursive_planner.py

Implements recursive route planning across grouped waypoints.
"""
import asyncio
from datetime import datetime
from typing import List
from models.route import TripPattern, WaypointGroup
from routing_engine.planning_cache import PlanningCache
from routing_engine.routing_context import RoutingContext
from routing_engine.mode_router import ModeRouter
from routing_engine.mode_expander import ModeExpander
from shared.pattern_utils import PatternUtils

class RecursivePlanner():
    """
    The planner processes grouped waypoints sequentially and recursively
    builds complete TripPattern objects.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes recursive planner with shared routing context.

        Args:
            context: RoutingContext containing route data and configuration
        """
        self.__ctx = context

        # Initialize route planning cache
        self.__cache = PlanningCache()

        # Router responsible for unimodal routing
        self.__mode_router = ModeRouter(self.__ctx)

        # Router responsible for multimodal groups branching
        self.__mode_expander = ModeExpander(self.__ctx)

    async def plan_groups(self, groups: List[WaypointGroup]) -> List[TripPattern]:
        """
        Entry point for recursive planning over waypoint groups.

        Args:
            groups: Ordered list of groups

        Returns:
            List of computed TripPattern objects 
        """
        # Combine selected date and time
        time_cursor = datetime.combine(self.__ctx.data.date, self.__ctx.data.time)

        # Recursive route planning
        return await self.__plan_recursive(
            groups,
            time_cursor,
            False,
            None
        )
    
    async def __plan_recursive(
        self,
        groups: List[WaypointGroup],
        time_cursor: datetime,
        bike_used: bool,
        partial_pattern: TripPattern | None
    ) -> List[TripPattern]:
        """
        Recursively processes waypoint groups and builds trip patterns.

        Args:
            groups: Remaining groups to process
            time_cursor: Current temporal reference datetime
            bike_used: Indicates, whether a bicycle has already been used
            partial_pattern: Partially computed trip pattern, the base pattern

        Returns:
            List of computed TripPattern objects
        """
        # No groups left to process
        if not groups:
            if partial_pattern:
                return [partial_pattern]
            return []
        
        # Extract currently processed group
        group = groups[0]
            
        # Handle multimodal branching
        if group.mode == "multimodal":
            # Expand multimodal group into concrete transport alternatives
            possible_groups = self.__mode_expander.expand_multimodal_group(
                group,
                partial_pattern is None,
                partial_pattern is not None and (bike_used or any(
                    leg.mode == "bicycle" 
                    for leg in partial_pattern.legs
                )),
            )

            # Recursively process each expanded branch in parallel
            tasks = [
                self.__plan_recursive(
                    group + groups[1:],
                    time_cursor,
                    bike_used,
                    partial_pattern
                )
                for group in possible_groups
            ]

            new_patterns = await asyncio.gather(*tasks)

            # Flatten nested results, List[List[TripPattern]] -> List[TripPattern]
            return self.__flatten_patterns(new_patterns)
        
        # Handle unimodal routing
        else:
            # Retrieve route results from cache or compute them
            results = await self.__cache.get_or_create_route(
                group,
                time_cursor,
                lambda: self.__mode_router.route_group(
                    group,
                    time_cursor
                )
            )

            # Assign mode list to each pattern
            for pattern in results:
                pattern.modes = [group.mode] * (len(group.waypoints) - 1)

            # Combine with previously computed partial pattern
            if partial_pattern:
                combined_patterns = PatternUtils.combine(
                    [partial_pattern],
                    [results],
                    self.__ctx.data.arrive_by
                )
            else:
                combined_patterns = results
            
            # Continue recursively with remaining groups
            tasks = [
                self.__plan_recursive(
                    groups[1:],
                    (
                        trip_pattern.legs[0].aimedStartTime 
                        if self.__ctx.data.arrive_by 
                        else trip_pattern.legs[-1].aimedEndTime
                    ),
                    # Update bicycle usage flag
                    bike_used or any(
                        leg.mode == "bicycle" 
                        for leg in trip_pattern.legs
                    ),
                    trip_pattern
                )
                for trip_pattern in combined_patterns
            ]

            new_patterns = await asyncio.gather(*tasks)

            # Flatten nested results, List[List[TripPattern]] -> List[TripPattern]
            return self.__flatten_patterns(new_patterns)

    @staticmethod
    def __flatten_patterns(results: List[List[TripPattern]]) -> List[TripPattern]:
        """
        Flattens nested list of TripPattern objects.

        Args:
            results: List of trip pattern lists

        Returns:
            Flattened list of TripPattern objects
        """
        return [
            pattern
            for result in results
            for pattern in result
        ]

# End of file recursive_planner.py
