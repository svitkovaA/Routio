"""
file: bicycle_public_router.py

Implements BicyclePublicRouter, the planning strategy designed to efficiently
handle multimodal route segments.
"""

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Coroutine, List, Tuple
from routers.router import Router
from shared.pattern_utils import PatternUtils
from routers.public_transport.public_transport_router import PublicTransportRouter
from routers.bicycles.bicycle_router import BicycleRouter
from routing_engine.routing_context import RoutingContext
from shared.geo_math import GeoMath
from models.route import TIME_DEPENDENT_MODES, Mode, TripPattern
from models.planning_context import PlanningContext
from routers.router_base import RouterBase

class BicyclePublicRouter(RouterBase, Router):
    """
    Router combining bicycle on the first route segment with a public transport
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
        Routes a trip using combined bicycle and public transport logic.

        Args:
            context: Planning context

        Returns:
            Combined trip patterns
        """
        # Split segment into potential bicycle group
        i, bike_group, distance = self.__split_bike_segment(context)

        # Entire route fits bicycle constraint, it is handled elsewhere
        if self.__fits_entire_bike(distance, i, context.waypoints):
            return []
    
        # Route with bicycle public transport combination
        return await self.__route_with_public(i, bike_group, distance, context)
    
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
            *self._parse_coordinates(waypoints[i - 1]),
            *self._parse_coordinates(waypoints[i])
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
            i: Index separating bicycle prefix and public transport suffix
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
            i: Index separating bicycle and public transport segments
            bike_group: Waypoints assigned to bicycle routing
            extra_distance: Overflow distance beyond allowed bicycle limit
            context: Planning context with time and route data

        Returns:
            Combined trip patterns after merging bicycle and public transport
        """
        # Compute interpolated starting point for bicycle routing
        lat, lon = GeoMath.interpolate_point(
            *self._parse_coordinates(bike_group[-1]),
            *self._parse_coordinates(context.waypoints[i]),
            extra_distance
        )

        # Store B coordinates for validating
        lat_b, lon_b = self._parse_coordinates(bike_group[-1])

        # Estimate public transport part duration
        time_offset = self._estimate_public_time_duration(context.waypoints[i-1:])

        # Route bicycle prefix directly
        bike_trip_patterns = await self.__bicycle_router.route_group(
            PlanningContext(
                # Add interpolated extra distance point
                waypoints=bike_group + [f"{lat}, {lon}"],
                time_cursor=context.time_cursor + time_offset,
                bicycle_public=True,
                use_bisector=True
            )
        )

        # Return empty if no bicycle routes found
        if not bike_trip_patterns:
            return []
        
        A_plane_routing = False
        bikeStationInfo = bike_trip_patterns[0].legs[-1].bikeStationInfo
        # Check if routing stays within the A plane
        if not bikeStationInfo or bikeStationInfo.bikeStations[0].in_A_plane:
            if extra_distance > 0.5:
                return []
            else:
                # Add B for routing
                i -= 1
            A_plane_routing = True

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
            public_start_index = 0

            # Locate boundary between public transport and bicycle segments
            for leg in pattern.legs:
                if leg.mode == "bicycle":
                    bike_leg_found = True
                # Stop at first non-bicycle leg after bicycle sequence
                elif bike_leg_found and leg.mode != "wait":
                    break

                public_start_index += 1

             # Check only the two legs before bicycle segment
            for leg in pattern.legs[public_start_index:public_start_index + 2]:
                # Accept if a public transport leg exists
                if leg.mode in TIME_DEPENDENT_MODES:
                    validate_patterns.append(pattern)
                    break

                to_place = leg.toPlace
                if not to_place:
                    continue

                # Discard if route reaches original waypoint without public transport
                if (
                    abs(to_place.latitude - lat_b) < 1e-6 and
                    abs(to_place.longitude - lon_b) < 1e-6
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
            i: Index separating bicycle and public transport segments
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
                *self._parse_coordinates(context.waypoints[i - 1]),
                *self._parse_coordinates(context.waypoints[i]),
                extra_distance * factor
            )

            new_waypoint = f"{lat}, {lon}"

            # Estimate public transport part duration
            time_offset = self._estimate_public_time_duration([new_waypoint] + context.waypoints[i:])

            # Attempt bicycle routing to interpolated point
            bike_trip_patterns = await self.__bicycle_router.route_group(
                PlanningContext(
                    waypoints=bike_group + [new_waypoint],
                    time_cursor=context.time_cursor + time_offset,
                    bicycle_public=True
                )
            )

            if bike_trip_patterns:
                # Compute total bicycle distance
                bike_distance = self._compute_bike_distance(
                    bike_trip_patterns[0]
                )

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
        Routes the bicycle prefix and combines it with the public transport
        suffix.

        Args:
            i: Index separating bicycle and public transport segments
            bike_trip_patterns: Computed bicycle trip patterns
            context: Planning context

        Returns:
            Combined multimodal trip patterns
        """
        # No valid bicycle result
        if not bike_trip_patterns:
            return []
        
        # Determine transfer point
        to_place = bike_trip_patterns[0].legs[-2].toPlace
        if to_place is None:
            return []

        # Route public transport suffix
        public_trip_patterns = await self.__public_router.route_group(
            PlanningContext(
                waypoints=[f"{to_place.latitude}, {to_place.longitude}"] + context.waypoints[i:],
                time_cursor=(
                    context.time_cursor
                    if self._ctx.data.arrive_by
                    else bike_trip_patterns[0].aimedEndTime
                )
            )
        )

        # Merge bicycle and public transport segments
        return PatternUtils.combine(
            bike_trip_patterns,
            [public_trip_patterns],
            False,                      # Always add public segments after bicycle ones
            bicycle_public=True
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
        waypoint_index, leg_index = self.__find_indices(pattern)

        public_leg_indices = self.__find_public_leg_indices(pattern, leg_index)

        bicycle_router = BicycleRouter(
            RoutingContext(
                self._ctx.data.model_copy(
                    update={
                        "arrive_by": True
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

        best_option = self.__select_best_option(bike_options, pattern.legs[0].aimedStartTime)

        if best_option:
            index, best_pattern = best_option
            print("improve: ", best_pattern.legs[0].aimedStartTime, pattern.legs[0].aimedStartTime, self._compute_bike_distance(best_pattern), self._compute_bike_distance(pattern))

            # Keep remaining legs after the replaced segment
            public_legs = deepcopy(pattern.legs[index:])

            return TripPattern(
                legs=best_pattern.legs + public_legs,
                aimedEndTime=public_legs[-1].aimedEndTime
            )

        return pattern

    @staticmethod
    def __find_indices(pattern: TripPattern) -> Tuple[int, int]:
        """
        Finds the split point in the trip pattern where bicycle segment ends
        and a time-dependent segment begins.

        Args:
            pattern: TripPattern to analyze

        Returns:
            Tuple (index of the last continuous time-independent segment,
            index of the wait leg after bicycle segment)
        """
        waypoint_index = 0
        leg_index = 1
        bike_found = pattern.legs[0].mode == "bicycle"
        prev_mode = pattern.legs[0].mode
        for leg in pattern.legs[1:]:
            # Count consecutive legs with the same time-independent mode
            if prev_mode == leg.mode and prev_mode not in TIME_DEPENDENT_MODES:
                waypoint_index += 1

            prev_mode = leg.mode

            # Mark bicycle segment start
            if leg.mode == "bicycle":
                bike_found = True

            leg_index += 1

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
        index = leg_index + 1
        prev_mode: Mode = "foot"
        for leg in pattern.legs[leg_index + 1:]:
            # Collect indices of time-dependent legs
            if leg.mode in TIME_DEPENDENT_MODES:
                public_leg_indices.append(index)

            # Iterate until waypoint
            if prev_mode == leg.mode and prev_mode not in TIME_DEPENDENT_MODES:
                break

            prev_mode = leg.mode

            index += 1

        return public_leg_indices

    @staticmethod
    def __select_best_option(
        options: List[Tuple[int, TripPattern | None]],
        best_time: datetime
    ) -> Tuple[int, TripPattern] | None:
        """
        Selects the best bicycle routing option based on departure time.

        Args:
            options: List of options (leg_index, resulting_pattern)
            best_time: Current best known departure time

        Returns:
            Tuple (index, pattern), or None if no improvement found
        """
        best_option: Tuple[int, TripPattern] | None = None

        for index, pattern in options:
            if pattern and pattern.legs[0].aimedStartTime > best_time:
                best_time = pattern.legs[0].aimedStartTime
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

            # Skip if starting location is missing
            if not leg.fromPlace:
                continue

            # Create new context ending at the start of the current leg
            ctx = PlanningContext(
                waypoints=context.waypoints[:waypoint_index + 1] + [
                    f"{leg.fromPlace.latitude}, {leg.fromPlace.longitude}"
                ],
                time_cursor=leg.aimedStartTime
            )

            # Enqueue async bicycle routing request
            tasks.append(bicycle_router.route_group(ctx))

        results = await asyncio.gather(*tasks)

        options: List[Tuple[int, TripPattern | None]] = []

        for idx, result in zip(public_leg_indices, results):
            # No route was found or bike distance is too long
            if (
                not result
                or self._compute_bike_distance(result[0]) > self._ctx.max_bike_distance * 1000 + 50
            ):
                options.append((idx, None))
                continue

            # Take best pattern
            bike_pattern = result[0]

            # Store index, computed distance, and pattern
            options.append((
                idx,
                bike_pattern
            ))

        return options

    def __fits_entire_bike(self, distance: float, i: int, waypoints: List[str]) -> bool:
        """
        Checks whether the entire route can be computed using bicycle.

        Args:
            distance: Total accumulated bicycle distance in kilometers
            i: Index of the last waypoint included in the bicycle segment
            waypoints: Full list of trip waypoint coordinates

        Returns:
            True if no public transport is needed, false otherwise
        """
        return i + 1 == len(waypoints) and distance <= self._ctx.max_bike_distance
    
    def __split_bike_segment(
        self,
        context: PlanningContext
    ) -> Tuple[int, List[str], float]:
        """
        Splits the waypoint sequence to find the longest bicycle segment possible.

        Args:
            context: Planning context

        Returns:
            Tuple (split_index, bike_group, accumulated_distance_km)
        """
        waypoints = context.waypoints
        
        i = 0
        bike_group: List[str] = []
        distance = 0

        # Create waypoint group to not exceed maximal allowed bicycle distance
        while i + 1 < len(waypoints) and distance <= self._ctx.max_bike_distance:
            bike_group.append(waypoints[i])
            distance += GeoMath.haversine_distance_km(
                *self._parse_coordinates(waypoints[i]),
                *self._parse_coordinates(waypoints[i + 1])
            ) * 1.2
            i += 1

        return i, bike_group, distance

    def _estimate_public_time_duration(self, waypoints: List[str]) -> timedelta:
        """
        Estimates public transport time waypoints in arrival mode.

        Args:
            waypoints: The waypoints between which the time is estimated

        Returns:
            Estimated time in arrival mode, zero in departure mode
        """
        if not self._ctx.data.arrive_by:
            return timedelta()
        
        return -super()._estimate_public_time_duration(waypoints)

# End of file bicycle_public_router.py
