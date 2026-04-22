"""
file: public_bicycle.py

Implements PublicBicycleRouter, the planning strategy designed to efficiently
handle multimodal route segments.
"""

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Coroutine, List, Tuple
from shared.pattern_utils import PatternUtils
from routers.router import Router
from shared.geo_math import GeoMath
from routing_engine.routing_context import RoutingContext
from models.route import TIME_DEPENDENT_MODES, Mode, TripPattern
from models.planning_context import PlanningContext
from routers.router_base import RouterBase
from routers.public_transport.public_transport_router import PublicTransportRouter
from routers.bicycles.bicycle_router import BicycleRouter

class PublicBicycleRouter(RouterBase, Router):
    """
    Router combining public transport on the first route segment with a bicycle
    on the second route segment.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes the combined router.

        Args:
            context: Global routing context
        """
        # Initialize base router context
        super().__init__(context)

        # Internal bicycle router
        self.__bicycle_router = BicycleRouter(self._ctx)

        # Internal public transport router
        self.__public_router = PublicTransportRouter(self._ctx)

    async def route_group(self, context: PlanningContext) -> List[TripPattern]:  
        """
        Routes a trip using combined public transport and bicycle logic.

        Args:
            context: Planning context

        Returns:
            Combined trip patterns
        """
        # Split segment into potential bicycle group
        i, bike_group, distance = self.__split_bike_segment(context)
        
        # Entire route fits bicycle constraint, it is handled elsewhere
        if self.__fits_entire_bike(distance, i):
            return []
        
        # Route with public transport bicycle combination
        return await self.__route_with_public(i, bike_group, distance, context)

    def __split_bike_segment(self, context: PlanningContext) -> Tuple[int, List[str], float]:
        """
        Splits the waypoint sequence to find the longest bicycle segment possible.

        Args:
            context: Planning context

        Returns:
            Tuple (split_index, bike_group, accumulated_distance_km)
        """
        waypoints = context.waypoints

        i = len(waypoints) - 1
        bike_group: List[str] = []
        distance = 0

        # Create waypoint group to not exceed maximal allowed bicycle distance
        while i > 0 and distance <= self._ctx.max_bike_distance:
            bike_group.insert(0, waypoints[i])
            distance += GeoMath.haversine_distance_km(
                *self._parse_coordinates(waypoints[i - 1]),
                *self._parse_coordinates(waypoints[i])
            ) * 1.2
            i -= 1

        return i, bike_group, distance

    def __fits_entire_bike(self, distance: float, i: int) -> bool:
        """
        Checks whether the entire route can be computed using bicycle.

        Args:
            distance: Total accumulated bicycle distance in kilometers
            i: Index of the last waypoint included in the bicycle segment

        Returns:
            True if no public transport is needed, false otherwise
        """
        return i == 0 and distance <= self._ctx.max_bike_distance
    
    def __compute_extra_distance(
        self,
        i: int,
        bike_group: List[str],
        distance: float,
        waypoints: List[str]
    ) -> float:
        """
        Computes how much the bicycle segment exceeds the allowed distance.

        Args:
            i: Index where bicycle segment ends
            bike_group: Waypoints included in bicycle segment
            distance: Total bicycle segment distance in km
            waypoints: Full waypoint list

        Returns:
            Extra distance beyond allowed bicycle distance
        """
        distance_to_next = distance - self._ctx.max_bike_distance

        # Single segment case
        if len(bike_group) == 1:
            return self._ctx.max_bike_distance
        
        # Compute remaining correction relative to next waypoint
        return GeoMath.haversine_distance_km(
            *self._parse_coordinates(waypoints[i]),
            *self._parse_coordinates(waypoints[i + 1])
        ) * 1.2 - distance_to_next
    
    async def __route_with_public(
        self,
        i: int,
        bike_group: List[str],
        distance: float,
        context: PlanningContext
    ) -> List[TripPattern]:
        """
        Chooses combined routing strategy based on extra distance.

        Args:
            i: Index separating public transport prefix and bicycle suffix
            bike_group: Waypoints forming the bicycle candidate segment
            distance: Accumulated bicycle distance in kilometers
            context: Planning context containing original waypoints and time

        Returns:
            Combined trip patterns
        """
        # Compute overflow distance beyond bicycle limit
        extra_distance = self.__compute_extra_distance(
            i,
            bike_group,
            distance,
            context.waypoints
        )

        # Very short adjustment, skip
        if len(bike_group) == 1 and extra_distance <= 1:
            return []

        # Small overflow, routing using first algorithm
        if extra_distance <= 1:
            return await self.__use_first_algorithm(
                i,
                bike_group,
                extra_distance,
                context
            )

        # Larger overflow, routing using second algorithm where interpolation is required
        return await self.__use_second_algorithm(
            i,
            bike_group,
            extra_distance,
            context
        )

    async def __use_first_algorithm(
        self,
        i: int,
        bike_group: List[str],
        extra_distance: float,
        context: PlanningContext
    ) -> List[TripPattern]:
        """
        Performs bicycle routing without interpolation.

        Args:
            i: Index separating public and bicycle segments
            bike_group: Waypoints assigned to bicycle routing
            extra_distance: Overflow distance beyond allowed bicycle limit
            context: Planning context with time and route data

        Returns:
            Combined trip patterns after merging bicycle and public transport
        """
        # Compute interpolated starting point for bicycle routing
        lat, lon = GeoMath.interpolate_point(
            *self._parse_coordinates(bike_group[0]),
            *self._parse_coordinates(context.waypoints[i]),
            extra_distance
        )

        # Store B coordinates for validation
        lat_b, lon_b = self._parse_coordinates(bike_group[0])

        # Estimate public transport part duration
        time_offset = self._estimate_public_time_duration(context.waypoints[:i + 2])

        # Route bicycle suffix directly from interpolated point
        bike_trip_patterns = await self.__bicycle_router.route_group(
            PlanningContext(
                waypoints=[f"{lat}, {lon}"] + bike_group,
                time_cursor=context.time_cursor + time_offset,
                public_bicycle=True,
                use_bisector=True
            )
        )

        # Return empty if no bicycle routes found
        if not bike_trip_patterns:
            return []
        
        A_plane_routing = False
        bikeStationInfo = bike_trip_patterns[0].legs[0].bikeStationInfo

        # Check if routing stays within the A plane
        if not bikeStationInfo or bikeStationInfo.bikeStations[1].in_A_plane:
            if extra_distance > 0.5:
                return []
            A_plane_routing = True
            i += 1

        
        # Combine bicycle suffix with public transport prefix
        trip_patterns = await self.__route_public_and_combine(
            i,
            bike_trip_patterns,
            context
        )

        # If not in A plane, skip validation
        if not A_plane_routing:
            return trip_patterns
        
        validate_patterns: List[TripPattern] = []

        # Validate combined routes to ensure proper public transport
        for pattern in trip_patterns:
            bike_leg_found = False
            public_end_index = len(pattern.legs) - 1

            # Locate boundary between public transport and bicycle segments
            for leg in reversed(pattern.legs):
                if leg.mode == "bicycle":
                    bike_leg_found = True

                # Stop at first non-bicycle leg after bicycle sequence
                elif bike_leg_found and leg.mode != "wait":
                    break

                public_end_index -= 1

            # Check only the two legs before bicycle segment
            for leg in pattern.legs[public_end_index - 1:public_end_index + 1]:
                
                # Accept if a public transport leg exists
                if leg.mode in TIME_DEPENDENT_MODES:
                    validate_patterns.append(pattern)
                    break

                from_place = leg.fromPlace
                if not from_place:
                    continue

                # Discard if route reaches original waypoint without public transport
                if (
                    abs(from_place.latitude - lat_b) < 1e-6 and
                    abs(from_place.longitude - lon_b) < 1e-6
                ):
                    break

        return validate_patterns

    async def __use_second_algorithm(
        self,
        i: int,
        bike_group: List[str],
        extra_distance: float,
        context: PlanningContext
    ) -> List[TripPattern]:
        """
        Uses interpolation to find a transfer point.

        Args:
            i: Index separating public and bicycle segments
            bike_group: Waypoints assigned to bicycle routing
            extra_distance: Overflow distance beyond allowed bicycle limit
            context: Planning context

        Returns:
            Combined trip patterns after merging bicycle and public transport
        """
        bike_trip_patterns: List[TripPattern] = []
        factor = 0.9
        step = 0.05

        # Iteratively search for feasible interpolation point
        while not bike_trip_patterns and factor >= 0.5:

            # Interpolate candidate transfer point
            lat, lon = GeoMath.interpolate_point(
                *self._parse_coordinates(context.waypoints[i + 1]),
                *self._parse_coordinates(context.waypoints[i]),
                extra_distance * factor
            )

            new_waypoint = f"{lat}, {lon}"

            # Estimate public transport part duration
            time_offset = self._estimate_public_time_duration(context.waypoints[:i + 1] + [new_waypoint])

            # Attempt bicycle routing from interpolated point
            bike_trip_patterns = await self.__bicycle_router.route_group(
                PlanningContext(
                    waypoints=[new_waypoint] + bike_group,
                    time_cursor=context.time_cursor + time_offset,
                    public_bicycle=True
                )
            )

            if bike_trip_patterns:
                # Compute total bicycle distance
                bike_distance = self._compute_bike_distance(bike_trip_patterns[0])

                # Validate bicycle constraint
                if bike_distance <= self._ctx.max_bike_distance * 1000 + 50:
                    bike_trip_patterns = [bike_trip_patterns[0]]
                else:
                    bike_trip_patterns = []

            # Reduce interpolation factor and retry
            factor -= step

        # Combine with public transport prefix
        trip_patterns = await self.__route_public_and_combine(
            i,
            bike_trip_patterns,
            context
        )

        # Return validated trip patterns
        return await asyncio.gather(*[
            self.__validate_pattern(context, pattern)
            for pattern in trip_patterns
        ])
    
    async def __route_public_and_combine(
        self,
        i: int,
        bike_trip_patterns: List[TripPattern],
        context: PlanningContext
    ) -> List[TripPattern]:
        """
        Routes the public transport prefix and combines it with
        the bicycle suffix.

        Args:
            i: Index separating public and bicycle segments
            bike_trip_patterns: Computed bicycle trip patterns
            context: Planning context

        Returns:
            Combined multimodal trip patterns
        """
        # No valid bicycle result
        if not bike_trip_patterns:
            return []
        
        # Determine transfer point
        from_place = bike_trip_patterns[0].legs[1].fromPlace
        if not from_place:
            return []
        
        # Route public transport prefix
        public_trip_patterns = await self.__public_router.route_group(
            PlanningContext(
                waypoints=context.waypoints[:i + 1] + [f"{from_place.latitude}, {from_place.longitude}"],
                time_cursor=(
                    bike_trip_patterns[0].legs[0].aimedStartTime
                    if self._ctx.data.arrive_by
                    else context.time_cursor
                )
            )
        )

        # Merge public and bicycle segments
        return PatternUtils.combine(
            bike_trip_patterns,
            [public_trip_patterns],
            True,
            public_bicycle=True
        )

    async def __validate_pattern(
        self,
        context: PlanningContext,
        pattern: TripPattern
    ) -> TripPattern:
        """
        Validates and potentially improves a trip pattern by replacing
        bicycle part of the route.

        Args:
            context: Planning context with waypoints and time
            pattern: Original trip pattern

        Returns:
            Updated TripPattern or original
        """
        waypoint_index, leg_index = self.__find_indices(context, pattern)

        public_leg_indices = self.__find_public_leg_indices(pattern, leg_index)

        bicycle_router = BicycleRouter(
            RoutingContext(
                self._ctx.data.model_copy(
                    update={
                        "arrive_by": False
                    }
                ),
                self._ctx.session
            )
        )

        bike_options = await self.__compute_bike_options(
            context,
            pattern,
            public_leg_indices,
            waypoint_index,
            bicycle_router
        )

        best_option = self.__select_best_option(bike_options, pattern.aimedEndTime)

        if best_option:
            index, best_pattern = best_option

            # Keep remaining legs before the replaced segment
            public_legs = deepcopy(pattern.legs[:index + 1])

            return TripPattern(
                legs=public_legs + best_pattern.legs,
                aimedEndTime=best_pattern.aimedEndTime
            )

        return pattern

    @staticmethod
    def __find_indices(
        context: PlanningContext,
        pattern: TripPattern
    ) -> Tuple[int, int]:
        """
        Finds the split point in the trip pattern where bicycle segment ends
        and a time-dependent segment begins.

        Args:
            pattern: TripPattern to analyze

        Returns:
            Tuple (index of the last continuous time-independent segment,
            index of the wait leg after bicycle segment)
        """
        waypoint_index = len(context.waypoints) - 1
        leg_index = len(pattern.legs) - 2
        bike_found = pattern.legs[-1].mode == "bicycle"
        prev_mode = pattern.legs[-1].mode
        for leg in reversed(pattern.legs[:-1]):
            # Count consecutive legs with the same time-independent mode
            if prev_mode == leg.mode and prev_mode not in TIME_DEPENDENT_MODES:
                waypoint_index -= 1

            prev_mode = leg.mode

            # Mark bicycle segment start
            if leg.mode == "bicycle":
                bike_found = True

            leg_index -= 1

            # Stop after first wait segment following bicycle one
            if bike_found and leg.mode == "wait":
                break
        
        return waypoint_index, leg_index

    @staticmethod
    def __find_public_leg_indices(
        pattern: TripPattern,
        leg_index: int
    ) -> List[int]:
        """
        Finds indices of time-dependent legs following a given split point.

        Args:
            pattern: TripPattern to analyze
            leg_index: Index from which to start searching

        Returns:
            List of indices corresponding to time-dependent legs
        """
        public_leg_indices: List[int] = []
        index = leg_index - 1
        prev_mode: Mode = "foot"
        for leg in reversed(pattern.legs[:leg_index]):
            # Collect indices of time-dependent legs
            if leg.mode in TIME_DEPENDENT_MODES:
                public_leg_indices.append(index)

            # Iterate until waypoint
            if prev_mode == leg.mode and prev_mode not in TIME_DEPENDENT_MODES:
                break

            prev_mode = leg.mode

            index -= 1

        return public_leg_indices

    @staticmethod
    def __select_best_option(
        options: List[Tuple[int, TripPattern | None]],
        best_time: datetime
    ) -> Tuple[int, TripPattern] | None:
        """
        Selects the best bicycle routing option based on arrival time.

        Args:
            options: List of options (leg_index, resulting_pattern)
            best_time: Current best known arrival time

        Returns:
            Tuple (index, pattern), or None if no improvement found
        """
        best_option: Tuple[int, TripPattern] | None = None

        for index, pattern in options:
            if pattern and pattern.aimedEndTime < best_time:
                best_time = pattern.aimedEndTime
                best_option = (index, pattern)

        return best_option

    async def __compute_bike_options(
        self,
        context: PlanningContext,
        pattern: TripPattern,
        public_leg_indices: List[int],
        waypoint_index: int,
        bicycle_router: BicycleRouter
    ) -> List[Tuple[int, TripPattern | None]]:
        """
        Computes alternative bicycle routes for selected public transport segments.

        Args:
            context: Planning context
            pattern: Trip pattern
            public_leg_indices: Indices of candidate legs for replacement
            waypoint_index: Index defining the prefix of waypoints to preserve

        Returns:
            List of tuples (index of the evaluated leg, bike pattern)
        """
        tasks: List[Coroutine[Any, Any, List[TripPattern]]] = []

        for index in public_leg_indices:
            # Candidate leg
            leg = pattern.legs[index]

            # Skip if destination location is missing
            if not leg.toPlace:
                continue

            # Create new context starting at the end of the current leg
            ctx = PlanningContext(
                waypoints=[
                    f"{leg.toPlace.latitude}, {leg.toPlace.longitude}"
                ] + context.waypoints[waypoint_index:],
                time_cursor=leg.aimedEndTime
            )

            # Enqueue async bicycle routing request
            tasks.append(bicycle_router.route_group(ctx))

        results = await asyncio.gather(*tasks)

        options: List[Tuple[int, TripPattern | None]] = []

        for idx, result in zip(public_leg_indices, results):
            # No route was found
            if (
                not result
                or self._compute_bike_distance(result[0]) > self._ctx.max_bike_distance * 1000 + 50
            ):
                options.append((idx, None))
                continue

            # Take best pattern
            bike_pattern = result[0]

            # Store index and pattern
            options.append((
                idx,
                bike_pattern
            ))

        return options

    def _estimate_public_time_duration(self, waypoints: List[str]) -> timedelta:
        """
        Estimates public transport time waypoints in departure mode.

        Args:
            waypoints: The waypoints between which the time is estimated

        Returns:
            Estimated time in departure mode, zero in arrival mode
        """
        if self._ctx.data.arrive_by:
            return timedelta()

        return super()._estimate_public_time_duration(waypoints)

# End of file public_bicycle_router.py
