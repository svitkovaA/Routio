
import asyncio
from datetime import datetime
from typing import List
from models.route import TIME_DEPENDENT_MODES, TripPattern, WaypointGroup
from routing_engine.planning_cache import PlanningCache
from routing_engine.routing_context import RoutingContext
from routing_engine.mode_router import ModeRouter
from routing_engine.mode_expander import ModeExpander
from shared.pattern_utils import PatternUtils

class RecursivePlanner():
    def __init__(self, context: RoutingContext):
        self.__ctx = context
        self.__cache = PlanningCache()
        self.__mode_router = ModeRouter(self.__ctx)
        self.__mode_expander = ModeExpander(self.__ctx)

    async def plan_groups(self, groups: List[WaypointGroup]) -> List[TripPattern]:
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
        # No groups to process
        if not groups:
            if partial_pattern:
                return [partial_pattern]
            return []
        
        # Multimodal group handling
        group = groups[0]
            
        if group.mode == "multimodal":
            # Expand multimodal group into concrete transport modes
            possible_groups = self.__mode_expander.expand_multimodal_group(
                group,
                partial_pattern is None,
                partial_pattern is not None and (bike_used or any(
                    leg.mode == "bicycle" 
                    for leg in partial_pattern.legs
                )),
            )

            # Recursively process each possible mode branch in parallel
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

            # Flatten List[List[TripPattern]] -> List[TripPattern]
            return self.__flatten_patterns(new_patterns)
        
        # Unimodal group handling
        else:
            # Route current segment with caching
            results = await self.__cache.get_or_create_route(
                group,
                time_cursor,
                lambda: self.__mode_router.route_group(
                    group,
                    time_cursor
                )
            )

            # Create pattern mode list
            for pattern in results:
                pattern.modes = [group.mode] * (len(group.group) - 1)

            # Combine with partial pattern if exists
            if partial_pattern:
                combined_patterns = PatternUtils.combine(
                    [partial_pattern],
                    [results],
                    self.__ctx.data.arrive_by,
                    partial_without_pt=not any(
                        leg.mode in TIME_DEPENDENT_MODES 
                        for leg in partial_pattern.legs
                    )
                )
            else:
                combined_patterns = results
            
            # Continue recursively for remaining groups
            tasks = [
                self.__plan_recursive(
                    groups[1:],
                    (
                        trip_pattern.legs[0].aimedStartTime 
                        if self.__ctx.data.arrive_by 
                        else trip_pattern.legs[-1].aimedEndTime
                    ),
                    bike_used or any(
                        leg.mode == "bicycle" 
                        for leg in trip_pattern.legs
                    ),
                    trip_pattern
                )
                for trip_pattern in combined_patterns
            ]

            new_patterns = await asyncio.gather(*tasks)

            # Flatten List[List[TripPattern]] -> List[TripPattern]
            return self.__flatten_patterns(new_patterns)

    @staticmethod
    def __flatten_patterns(results: List[List[TripPattern]]) -> List[TripPattern]:
        return [
            pattern
            for result in results
            for pattern in result
        ]
