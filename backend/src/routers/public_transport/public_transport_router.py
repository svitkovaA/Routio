"""
file: public_transport_router.py

Implements the public transport routing layer.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Tuple
from routers.router import Router
from routers.public_transport.enrichers.gtfs_enricher import GTFSEnricher
from routers.public_transport.enrichers.lissy_enricher import LissyEnricher
from routers.public_transport.enrichers.enricher_base import EnricherBase
from routers.router_base import RouterBase
from models.route import Leg, Place, PointOnLink, TripPattern
from models.planning_context import PlanningContext
from otp.public_transport import OTPPublicTransport
from routing_engine.routing_context import RoutingContext
from shared.pattern_utils import PatternUtils
from shared.geo_math import GeoMath

class PublicTransportRouter(RouterBase, Router):
    """
    Public transport routing coordinator.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes the public transport router.

        Args:
            context: Routing context containing configuration
        """
        super().__init__(context)

        # OTP public transport client
        self.__otp_client = OTPPublicTransport(self._ctx)

        # Register enrichers applied after routing
        self.__enrichers: List[EnricherBase] = [
            GTFSEnricher(),
            LissyEnricher(self._ctx.data.use_historical_delays)
        ]

    async def route_group(self, context: PlanningContext) -> List[TripPattern]:
        """
        Routes a sequence of waypoints using public transport.

        Args:
            context: Planning context with waypoints and time information

        Returns:
            List of computed and enriched trip patterns
        """
        trip_patterns: List[TripPattern] = []
        num_of_waypoints = len(context.waypoints)
        is_first_part = True

        # Not enough waypoints to build a route
        if num_of_waypoints < 2:
            return []
        
        if self._ctx.data.arrive_by:
            # Start from last waypoint in arrival mode
            i = num_of_waypoints - 1

            while i > 0:
                # Build next logical waypoint group
                group, i, short_source = self.__build_next_group_arrive(context.waypoints, i)

                # Route longer public transport segment, direct foot is not allowed
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
                # Build next logical waypoint group
                group, i, short_target = self.__build_next_group_depart(context.waypoints, i)

                # Route longer public transport segment, direct foot is not allowed
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
        """
        Applies all enrichers sequentially to a trip pattern.

        Args:
            trip_pattern: Trip pattern to enrich
        """
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
        """
        Routes a group of waypoints and combines results with existing partial
        patterns.

        Args:
            waypoints: Waypoints in the current group
            total_num_of_pt_waypoints: Total waypoint count in original request
            trip_patterns: Previously computed partial patterns
            time_cursor: Reference time for routing
            is_first_part: Indicates, whether this is the first routed group
            allow_direct_foot: Indicates, whether direct foot routing is allowed

        Returns:
            Combined list of trip patterns
        """
        # Build routing tasks depending on existing partial patterns
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
    
        # Combine new results with partial ones
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
        """
        Builds next logical waypoint group in departure mode. Groups waypoints
        until distance threshold is violated.

        Returns:
            Tuple (group, new_index, short_target)
        """
        group: List[str] = []
        distance = 10.0         # Dummy value bigger than threshold

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
        """
        Builds next logical waypoint group in arrival mode. Groups waypoints
        in reverse order until threshold is violated.

        Returns:
            Tuple (group, new_index, short_source)
        """
        group: List[str] = []
        distance = 10.0         # Dummy value bigger than threshold

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
        """
        Computes haversine distance between two coordinate strings.

        Args:
            a: Coordinate string in format lat,lon
            b: Coordinate string in format lat,lon

        Returns:
            Distance in kilometers
        """
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
        """
        Routes all consecutive waypoint segments within a single waypoint group.

        Args:
            waypoints: Waypoints of the current group
            total_num_of_pt_waypoints: Total waypoint count in the original request
            time_cursor: Reference time
            allow_direct_foot: Indicates, whether direct foot routing is allowed for this group

        Returns:
            List of trip patterns representing computed routes for this group
        """
        # Determine segment routing order based on mode
        indices = (
            list(reversed(range(len(waypoints) - 1)))
            if self._ctx.data.arrive_by
            else range(len(waypoints) - 1)
        )

        # Track whether the first segment of this group is being routed
        is_first_part = True
        trip_patterns: List[TripPattern] = []

        # Route each consecutive segment and extend partial patterns
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

            # After the first segment, subsequent segments must combine results
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
        """
        Routes a single segment using OTP and merges result.

        Args:
            origin: Segment origin coordinates in format lat, lon
            destination: Segment destination coordinates in format lat, lon
            total_num_of_pt_waypoints: Total waypoint count in the original request
            time_cursor: Reference time
            partial_patterns: Already built partial trip patterns to extend
            is_first_part: Indicates, whether this is the first routed segment in the group
            allow_direct_foot: Indicates, whether direct foot routing is allowed for this segment

        Returns:
            Updated list of trip patterns after adding this segment
        """
        # Build OTP routing tasks based on existing partial patterns
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
        # Initial OTP request for first segment
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

        # Reduce OTP alternatives by signature and select best timing per signature
        selected_patterns = [
            self.__select_best_patterns(
                trip_patterns,
                total_num_of_pt_waypoints
            )
            for trip_patterns in results
        ]

        # Insert artificial foot legs
        for patterns in selected_patterns:
            for pattern in patterns:
                # Insert first leg
                if pattern.legs[0].mode != "foot":
                    from_place = pattern.legs[0].fromPlace
                    if from_place:
                        pattern.legs.insert(
                            0,
                            self.__prepare_artificial_leg(
                                from_place,
                                pattern.legs[0].aimedStartTime
                            )
                        )
                
                # Insert last leg
                if pattern.legs[-1].mode != "foot":
                    to_place = pattern.legs[-1].toPlace
                    if to_place:
                        pattern.legs.append(
                            self.__prepare_artificial_leg(
                                to_place,
                                pattern.legs[-1].aimedEndTime
                            )
                        )

        # First segment produces patterns directly without combining
        if not partial_patterns and is_first_part:
            return selected_patterns[0]
        
        # Combine newly routed segment patterns with previous partial patterns
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
        """
        Selects a reduced set of trip patterns from OTP results.

        Args:
            trip_patterns: Trip patterns for a single segment
            total_num_of_pt_waypoints: Total waypoint count in the original request

        Returns:
            Reduced list of selected trip patterns
        """
        # Group patterns by line/mode signature to eliminate results differentiated only in time
        patterns_map: Dict[str, List[TripPattern]] = {}

        for pattern in trip_patterns:
            # Build signature describing the used modes/lines
            key = ""
            for leg in pattern.legs:
                if leg.mode in ["foot", "bicycle"]:
                    key += f"-{leg.mode[0]}"
                elif leg.line:
                    key += f"-{leg.line.publicCode}"

            # Append pattern under its signature
            patterns_map.setdefault(key, []).append(pattern)

        # Select best pattern per signature based on routing direction
        new_trip_patterns: List[TripPattern] = []
        for item in patterns_map.values():
            if self._ctx.data.arrive_by:
                # Prefer latest departure while still arriving by the target time
                best = max(item, key=lambda p: p.legs[0].aimedStartTime)
            else:
                # Prefer earliest arrival in departure planning
                best = min(item, key=lambda p: p.aimedEndTime)

            new_trip_patterns.append(best)

        # Limit number of trip patterns to avoid extreme growth
        return new_trip_patterns[:self.__max_patterns_limit(total_num_of_pt_waypoints)]

    @staticmethod
    def __max_patterns_limit(count: int) -> int:
        """
        Defines maximal number of public transport trip patterns per total
        waypoint count.

        Args:
            count: Total number of public transport waypoints

        Returns:
            Maximum allowed trip pattern count
        """
        pt_number_th = [0, 0, 5, 3, 2]

        if count >= len(pt_number_th):
            return pt_number_th[-1]
        
        return pt_number_th[count]

    @staticmethod
    def __prepare_artificial_leg(place: Place, time: datetime) -> Leg:
        """
        Prepares artificial leg.

        Args:
            node: Bike station node

        Returns:
            Leg as artificial segment
        """
        return Leg(
            mode="foot",
            duration=0,
            pointsOnLink=PointOnLink(points=[]),
            fromPlace=Place(
                latitude=place.latitude,
                longitude=place.longitude
            ),
            toPlace=Place(
                latitude=place.latitude,
                longitude=place.longitude
            ),
            artificial=True,
            aimedStartTime=time,
            aimedEndTime=time
        )

# End of file public_transport_router.py
