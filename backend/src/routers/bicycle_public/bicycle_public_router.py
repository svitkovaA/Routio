"""
file: bicycle_public_router.py

Implements BicyclePublicRouter, the planning strategy designed to efficiently
handle multimodal route segments.
"""

from typing import List, Tuple
from routers.router import Router
from shared.pattern_utils import PatternUtils
from routers.public_transport.public_transport_router import PublicTransportRouter
from routers.bicycles.bicycle_router import BicycleRouter
from routing_engine.routing_context import RoutingContext
from shared.geo_math import GeoMath
from models.route import TripPattern
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
        ) - distance_to_next
    
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
        context: PlanningContext
    ) -> List[TripPattern]:
        """
        Performs bicycle routing without interpolation.

        Args:
            i: Index separating bicycle and public transport segments
            bike_group: Waypoints assigned to bicycle routing
            context: Planning context with time and route data

        Returns:
            Combined trip patterns after merging bicycle and public transport
        """
        # Route bicycle prefix directly
        bike_trip_patterns = await self.__bicycle_router.route_group(
            PlanningContext(
                waypoints=bike_group,
                time_cursor=context.time_cursor,
                bicycle_public=True
            )
        )

        # Combine with public transport suffix
        return await self.__route_public_and_combine(
            i,
            bike_trip_patterns,
            context
        )

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

            # Attempt bicycle routing to interpolated point
            bike_trip_patterns = await self.__bicycle_router.route_group(
                PlanningContext(
                    waypoints=bike_group + [new_waypoint],
                    time_cursor=context.time_cursor,
                    bicycle_public=True
                )
            )

            if bike_trip_patterns:
                bike_distance = 0
                # Compute total bicycle distance
                for leg in bike_trip_patterns[0].legs:
                    if leg.mode == "bicycle":
                        bike_distance += leg.distance

                # Validate bicycle constraint
                if bike_distance <= self._ctx.max_bike_distance * 1000 + 50:
                    bike_trip_patterns = [bike_trip_patterns[0]]
                else:
                    bike_trip_patterns = []

            # Reduce interpolation factor and retry
            factor -= step

        # Combine with public transport suffix
        return await self.__route_public_and_combine(
            i,
            bike_trip_patterns,
            context
        )

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
            False                      # Always add public segments after bicycle ones
        )

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
        return i + 1 == len(waypoints) and distance * 1.2 <= self._ctx.max_bike_distance
    
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
        while i + 1 < len(waypoints) and distance * 1.2 <= self._ctx.max_bike_distance:
            bike_group.append(waypoints[i])
            distance += GeoMath.haversine_distance_km(
                *self._parse_coordinates(waypoints[i]),
                *self._parse_coordinates(waypoints[i + 1])
            )
            i += 1

        return i, bike_group, distance

# End of file bicycle_public_router.py
