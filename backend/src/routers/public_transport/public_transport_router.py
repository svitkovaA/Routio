import asyncio
from datetime import datetime
from typing import Dict, List, Tuple
from routers.router import Router
from routers.public_transport.enrichers.gtfs_enricher import GTFSEnricher
from routers.public_transport.enrichers.lissy_enricher import LissyEnricher
from routers.public_transport.enrichers.enricher_base import EnricherBase
from routers.router_base import RouterBase
from models.route import TripPattern
from models.planning_context import PlanningContext
from otp.public_transport import OTPPublicTransport
from routing_engine.routing_context import RoutingContext
from shared.pattern_utils import PatternUtils
from shared.geo_math import GeoMath
# from services.public_transport_service.process_public_route import process_public_route

class PublicTransportRouter(RouterBase, Router):
    def __init__(self, context: RoutingContext):
        super().__init__(context)
        self.__otp_client = OTPPublicTransport(self._ctx)

        # Register enrichers applied after routing
        self.__enrichers: List[EnricherBase] = [
            GTFSEnricher(),
            LissyEnricher()
        ]

    async def route_group(self, context: PlanningContext) -> List[TripPattern]:
        # return await process_public_route(
        #     context.waypoints,
        #     context.time_cursor,
        #     self._ctx.data.arrive_by,
        #     self._ctx.data.max_transfers,
        #     self._ctx.data.selected_modes,
        #     self._ctx.data.walk_speed,
        #     self._ctx.session
        # )

        trip_patterns: List[TripPattern] = []
        num_of_waypoints = len(context.waypoints)
        is_first_part = True

        # Return empty if less than two waypoints
        if num_of_waypoints < 2:
            return []
        
        if self._ctx.data.arrive_by:
            # Start from last waypoint in arrive_by mode
            i = num_of_waypoints - 1

            while i > 0:
                # Build next logical group of waypoints
                group, i, short_source = self.__build_next_group_arrive(context.waypoints, i)

                # Route longer public transport segment (direct foot is not allowed)
                if len(group) > 1:
                    trip_patterns = await self.__route_group_and_combine(
                        group,
                        num_of_waypoints,
                        trip_patterns,
                        context.time_cursor,
                        is_first_part
                    )
                
                # Route shorter segment with allowed direct foot
                if short_source is not None and group:
                    trip_patterns = await self.__route_group_and_combine(
                        [short_source, group[0]],
                        num_of_waypoints,
                        trip_patterns,
                        context.time_cursor,
                        is_first_part,
                        allow_direct_foot=True
                    )
                is_first_part = False
        else:
            # Start from first waypoint in departure mode
            i = 0

            while i + 1 < num_of_waypoints:
                # Build next logical group of waypoints
                group, i, short_target = self.__build_next_group_depart(context.waypoints, i)

                # Route longer public transport segment (direct foot is not allowed)
                if len(group) > 1:
                    trip_patterns = await self.__route_group_and_combine(
                        group,
                        num_of_waypoints,
                        trip_patterns,
                        context.time_cursor,
                        is_first_part
                    )
                
                # Route shorter segment with allowed direct foot
                if short_target is not None and group:
                    trip_patterns = await self.__route_group_and_combine(
                        [group[-1], short_target],
                        num_of_waypoints,
                        trip_patterns,
                        context.time_cursor,
                        is_first_part,
                        allow_direct_foot=True
                    )
                is_first_part = False
        
        # Enrich all trip patterns
        tasks = [
            self.__enrich_pattern(pattern)
            for pattern in trip_patterns
        ]
        await asyncio.gather(*tasks)

        return trip_patterns
    
    async def __enrich_pattern(self, trip_pattern: TripPattern) -> None:
        # Sequentially apply all enrichers to pattern
        for enricher in self.__enrichers:
            await enricher.enrich(trip_pattern)

    async def __route_group_and_combine(
        self,
        waypoints: List[str],
        total_num_of_pt_waypoints: int,
        trip_patterns: List[TripPattern],
        time_cursor: datetime,
        is_first_part: bool,
        allow_direct_foot: bool = False
    ) -> List[TripPattern]:
        # Build routing tasks based on existing partial patterns
        if trip_patterns:
            tasks = [
                self.__route_group_segments(
                    waypoints,
                    total_num_of_pt_waypoints,
                    (
                        pattern.legs[0].aimedStartTime
                        if self._ctx.data.arrive_by
                        else pattern.aimedEndTime
                    ),
                    allow_direct_foot
                )
                for pattern in trip_patterns
            ]
        # Initial routing
        else:
            tasks = [
                self.__route_group_segments(
                    waypoints,
                    total_num_of_pt_waypoints,
                    time_cursor,
                    allow_direct_foot
                )
            ]
        
        results = await asyncio.gather(*tasks)

        # Return first segment result directly
        if not trip_patterns and is_first_part:
            return results[0]
    
        # Combine partial and new results
        return PatternUtils.combine(
            trip_patterns,
            results,
            self._ctx.data.arrive_by
        )
    
    @staticmethod
    def __build_next_group_depart(
        waypoints: List[str],
        i: int,
        threshold_km: float = 1.0
    ) -> Tuple[List[str], int, str | None]:
        group: List[str] = []
        distance = 10.0    # Dummy value bigger than threshold

        # Collect consecutive waypoints beyond distance threshold
        while distance >= threshold_km and i + 1 < len(waypoints):
            group.append(waypoints[i])
            distance = PublicTransportRouter.__compute_distance_km(waypoints[i], waypoints[i + 1])
            i += 1

        # Include last waypoint if threshold condition is fulfilled
        if distance >= threshold_km:
            group.append(waypoints[i])
            i += 1

        # Identify short segment
        short_target = waypoints[i] if i < len(waypoints) else None
        return group, i, short_target

    @staticmethod
    def __build_next_group_arrive(
        waypoints: List[str],
        i: int,
        threshold_km: float = 1.0
    ) -> Tuple[List[str], int, str | None]:
        group: List[str] = []
        distance = 10.0     # Dummy value bigger than threshold

        # Collect consecutive waypoints beyond distance threshold in reverse direction
        while distance >= threshold_km and i > 0:
            group.insert(0, waypoints[i])
            distance = PublicTransportRouter.__compute_distance_km(waypoints[i - 1], waypoints[i])
            i -= 1

        # Include previous waypoint if threshold condition is fulfilled
        if distance >= threshold_km:
            group.insert(0, waypoints[i])
            i -= 1

        # Identify short segment
        short_source = waypoints[i] if i >= 0 else None
        return group, i, short_source
    
    @staticmethod
    def __compute_distance_km(a: str, b: str) -> float:
        # Compute haversine distance between two coordinates
        return GeoMath.haversine_distance_km(
            *PublicTransportRouter._parse_coordinates(a),
            *PublicTransportRouter._parse_coordinates(b)
        )

    async def __route_group_segments(
        self,
        waypoints: List[str],
        total_num_of_pt_waypoints: int,
        time_cursor: datetime,
        allow_direct_foot: bool
    ) -> List[TripPattern]:
        # Determine routing order based on mode
        indices = (
            list(reversed(range(len(waypoints) - 1)))
            if self._ctx.data.arrive_by
            else range(len(waypoints) - 1)
        )

        is_first_part = True
        trip_patterns = []

        # Route each segment within group
        for index in indices:
            trip_patterns = await self.__route_segment(
                self._parse_coordinates(waypoints[index]),
                self._parse_coordinates(waypoints[index + 1]),
                total_num_of_pt_waypoints,
                time_cursor,
                trip_patterns,
                is_first_part,
                allow_direct_foot
            )
            is_first_part = False

        return trip_patterns
    
    async def __route_segment(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        total_num_of_pt_waypoints: int,
        time_cursor: datetime,
        partial_patterns: List[TripPattern],
        is_first_part: bool,
        allow_direct_foot: bool
    ) -> List[TripPattern]:
        # Build OTP routing tasks based on partial patterns
        if partial_patterns:
            tasks = [
                self.__otp_client.execute(
                    origin,
                    destination,
                    (
                        pattern.legs[0].aimedStartTime
                        if self._ctx.data.arrive_by
                        else pattern.aimedEndTime
                    ),
                    allow_direct_foot
                )
                for pattern in partial_patterns
            ]
        # Initial OTP routing
        else:
            tasks = [
                self.__otp_client.execute(
                    origin,
                    destination,
                    time_cursor,
                    allow_direct_foot
                )
            ]

        results = await asyncio.gather(*tasks)

        # Postprocess each OTP result
        selected_patterns = [
            self.__select_best_patterns(
                trip_patterns,
                total_num_of_pt_waypoints
            )
            for trip_patterns in results
        ]

        # Return first segment result directly
        if not partial_patterns and is_first_part:
            return selected_patterns[0]
        
        # Combine partial and new results
        return PatternUtils.combine(
            partial_patterns,
            selected_patterns,
            self._ctx.data.arrive_by
        )

    def __select_best_patterns(
        self,
        trip_patterns: List[TripPattern],
        total_num_of_pt_waypoints: int
    ) -> List[TripPattern]:
        # Group patterns by line/mode signature to eliminate results differentiated only in time
        patterns_map: Dict[str, List[TripPattern]] = {}

        for pattern in trip_patterns:
            key = ""
            for leg in pattern.legs:
                if leg.mode in ["foot", "bicycle"]:
                    key += f"-{leg.mode[0]}"
                elif leg.line:
                    key += f"-{leg.line.publicCode}"

            patterns_map.setdefault(key, []).append(pattern)

        # Select best pattern per signature based on routing direction
        new_trip_patterns: List[TripPattern] = []
        for item in patterns_map.values():
            if self._ctx.data.arrive_by:
                best = max(item, key=lambda p: p.legs[0].aimedStartTime)
            else:
                best = min(item, key=lambda p: p.aimedEndTime)
            new_trip_patterns.append(best)

        # Limit number of trip patterns to avoid combinatorial explosion
        return new_trip_patterns[:self.__max_patterns_limit(total_num_of_pt_waypoints)]

    @staticmethod
    def __max_patterns_limit(count: int) -> int:
        # Define max number of PT results per total waypoint count
        pt_number_th = [0, 0, 5, 3, 2]

        if count >= len(pt_number_th):
            return pt_number_th[-1]
        
        return pt_number_th[count]
