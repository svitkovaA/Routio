from typing import List, Tuple
from shared.pattern_utils import PatternUtils
from routers.router import Router
from shared.geo_math import GeoMath
from routing_engine.routing_context import RoutingContext
from models.route import TripPattern
from models.planning_context import PlanningContext
from routers.router_base import RouterBase
from routers.public_transport.public_transport_router import PublicTransportRouter
from routers.bicycles.bicycle_router import BicycleRouter

class PublicBicycleRouter(RouterBase, Router):
    def __init__(self, context: RoutingContext):
        super().__init__(context)
        self.__bicycle_router = BicycleRouter(self._ctx)
        self.__public_router = PublicTransportRouter(self._ctx)

    async def route_group(self, context: PlanningContext) -> List[TripPattern]:    
        i, bike_group, distance = self.__split_bike_segment(context)
        
        if self.__fits_entire_bike(distance, i):
            return []
        return await self.__route_with_public(i, bike_group, distance, context)

    def __split_bike_segment(self, context: PlanningContext) -> Tuple[int, List[str], float]:
        waypoints = context.waypoints

        i = len(waypoints) - 1
        bike_group: List[str] = []
        distance = 0

        # Create waypoint group to not exceed maximal allowed bicycle distance
        while i > 0 and distance * 1.2 <= self._ctx.max_bike_distance:
            bike_group.insert(0, waypoints[i])
            distance += GeoMath.haversine_distance_km(
                *self._parse_coordinates(waypoints[i - 1]),
                *self._parse_coordinates(waypoints[i])
            )
            i -= 1

        return i, bike_group, distance

    def __fits_entire_bike(self, distance: float, i: int) -> bool:
        return i == 0 and distance * 1.2 <= self._ctx.max_bike_distance
    
    def __compute_extra_distance(
        self,
        i: int,
        bike_group: List[str],
        distance: float,
        waypoints: List[str]
    ) -> float:
        distance_to_next = distance - self._ctx.max_bike_distance

        if len(bike_group) == 1:
            return self._ctx.max_bike_distance
        
        return GeoMath.haversine_distance_km(
            *self._parse_coordinates(waypoints[i]),
            *self._parse_coordinates(waypoints[i + 1])
        ) - distance_to_next
    
    async def __route_with_public(
        self,
        i: int,
        bike_group: List[str],
        distance: float,
        context: PlanningContext
    ) -> List[TripPattern]:
        extra_distance = self.__compute_extra_distance(
            i,
            bike_group,
            distance,
            context.waypoints
        )

        # Very short adjustment, skip
        if len(bike_group) == 1 and extra_distance <= 1:
            return []

        if extra_distance <= 1:
            return await self.__use_first_algorithm(
                i,
                bike_group,
                context
            )

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
        bike_trip_patterns = await self.__bicycle_router.route_group(
            PlanningContext(
                waypoints=bike_group,
                time_cursor=context.time_cursor,
                public_bicycle=True
            )
        )

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
        bike_trip_patterns: List[TripPattern] = []
        factor = 0.9
        step = 0.05

        while not bike_trip_patterns and factor >= 0.5:
            lat, lon = GeoMath.interpolate_point(
                *self._parse_coordinates(context.waypoints[i + 1]),
                *self._parse_coordinates(context.waypoints[i]),
                extra_distance * factor
            )

            new_waypoint = f"{lat}, {lon}"

            bike_trip_patterns = await self.__bicycle_router.route_group(
                PlanningContext(
                    waypoints=[new_waypoint] + bike_group,
                    time_cursor=context.time_cursor,
                    public_bicycle=True
                )
            )

            if bike_trip_patterns:
                bike_distance = 0
                for leg in bike_trip_patterns[0].legs:
                    # Compute total bicycle distance
                    if leg.mode == "bicycle":
                        bike_distance += leg.distance

                # Validate bicycle constraints
                if bike_distance <= self._ctx.max_bike_distance * 1000 + 50:
                    bike_trip_patterns = [bike_trip_patterns[0]]
                else:
                    bike_trip_patterns = []

            # Reduce interpolation factor and retry
            factor -= step

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
        if not bike_trip_patterns:
            return []
        
        from_place = bike_trip_patterns[0].legs[1].fromPlace
        if not from_place:
            return []
        
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

        return PatternUtils.combine(
            bike_trip_patterns,
            [public_trip_patterns],
            True,
            partial_without_pt=True
        )
