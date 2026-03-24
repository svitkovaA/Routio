"""
file: station_changer.py

Contains logic for recalculating a trip pattern after a user changes the
selected bicycle station or bike rack.
"""

from copy import deepcopy
from datetime import datetime
from typing import List, Literal, Tuple
from fastapi import HTTPException
from gql.client import AsyncClientSession
from api.route.station_changer_context import StationChangerContext
from otp.foot import OTPFoot
from otp.bicycle import OTPBicycle
from routing_engine.routing_engine import RoutingEngine
from models.route_data import LegPreferences
from shared.pattern_utils import PatternUtils
from shared.geo_math import GeoMath
from shared.leg_utils import LegUtils
from models.route import (
    TIME_INDEPENDENT_MODES,
    BikeStationInfo,
    Leg,
    Mode,
    Place,
    PlaceBase,
    PointOnLink,
    RoutingMode,
    TripPattern
)
from routing_engine.routing_context import RoutingContext
from models.bike_station_data import BikeStationData

class StationChanger():
    """
    Handles recalculation of trip pattern after bicycle station change.
    """
    def __init__(self, data: BikeStationData,  session: AsyncClientSession):
        """
        Initializes StationChanger with routing context and OTP clients.

        Args:
            data: Request payload
            session: GraphQL session used for OTP queries
        """
        # Routing configuration context
        self.__routing_ctx = RoutingContext(data.route_data, session)

        # Internal station change context
        self.__ctx = StationChangerContext(data)

        # Bicycle OTP client
        self.__otp_bicycle_client = OTPBicycle(self.__routing_ctx)

        # Foot OTP client
        self.__otp_foot_client = OTPFoot(self.__routing_ctx)

    async def change_bike_station(self) -> TripPattern:
        """
        Rebuilds trip pattern after bike station selection change.

        Returns:
            Rebuild trip pattern with recalculated legs
        """
        # Routing backwards in arrival mode
        if self.__routing_ctx.data.arrive_by:
            return await self.__rebuild_pattern_arrival()
        
        # Routing forward in departure mode
        else:
            return await self.__rebuild_pattern_departure()

    async def __rebuild_pattern_departure(self) -> TripPattern:
        """
        Rebuilds trip pattern after bike station change

        Returns:
            Updated TripPattern with recalculated prefix and timing.
        """
        legs = self.__ctx.data.original_legs

        # Identify where route needs rebuilding
        leg_index, waypoint_count = self.__find_affected_segment_departure()

        # Preserve unaffected suffix of the original route
        base_legs = deepcopy(legs[:leg_index+1])
        leg_index = len(base_legs)

        # Build updated station prefix
        new_legs = await self.__build_station_prefix(leg_index)

        # Prepare routing data
        if self.__ctx.data.origin_bike_station:
            waypoint_group, routing_modes = await self.__prepare_waypoint_connection_origin_departure(
                new_legs,
                leg_index,
                waypoint_count
            )
        else:
            waypoint_group, routing_modes = await self.__prepare_waypoint_connection_destination_departure(
                new_legs,
                leg_index,
                waypoint_count
            )

        normalized_routing_modes = self.__normalize_modes(routing_modes)

        # Adjust times in legs to eliminate gaps
        self.__justify_segment(new_legs)

        # Recalculate affected part using routing engine
        rerouted_prefix_pattern = await self.__route_changed_part(
            normalized_routing_modes,
            waypoint_group,
            new_legs[-1].aimedEndTime
        )

        # Merge preserved base with rebuilt prefix
        return self.__merge_with_base_departure(
            rerouted_prefix_pattern,
            new_legs,
            base_legs
        )

    async def __rebuild_pattern_arrival(self) -> TripPattern:
        """
        Rebuilds trip pattern after bike station change

        Returns:
            Updated TripPattern with recalculated suffix and timing.
        """
        legs = self.__ctx.data.original_legs

         # Identify where route needs rebuilding
        leg_index, waypoint_count = self.__find_affected_segment_arrival()

        # Preserve unaffected suffix of the original route
        base_legs = deepcopy(legs[leg_index + 1:])
        leg_index = len(legs) - len(base_legs) - 1

        # Build updated station suffix
        new_legs = await self.__build_station_suffix(leg_index)

         # Prepare routing data
        if self.__ctx.data.origin_bike_station:
            waypoint_group, routing_modes = await self.__prepare_waypoint_connection_origin_arrival(
                new_legs,
                leg_index,
                waypoint_count
            )
        else:
            waypoint_group, routing_modes = await self.__prepare_waypoint_connection_destination_arrival(
                new_legs,
                leg_index,
                waypoint_count
            )

        normalized_routing_modes = self.__normalize_modes(routing_modes)

        # Adjust times in legs to eliminate gaps
        self.__justify_segment(new_legs)

        # Recalculate affected part using routing engine
        rerouted_prefix_pattern = await self.__route_changed_part(
            normalized_routing_modes,
            waypoint_group,
            new_legs[0].aimedStartTime
        )

        # Merge preserved base with rebuilt prefix
        return self.__merge_with_base_arrival(
            rerouted_prefix_pattern,
            new_legs,
            base_legs
        )

    def __merge_with_base_arrival(
        self,
        routed_suffix_pattern: TripPattern | None,
        new_legs: List[Leg],
        base_legs: List[Leg]
    ) -> TripPattern:
        """
        Merges rerouted suffix with new legs and preserved base legs.

        Args:
            routed_suffix_pattern: Result of rerouted suffix
            new_legs: Newly constructed legs caused by bike station change
            base_legs: Unaffected prefix of original trip pattern

        Returns:
            Newly constructed TripPattern with merged legs and updated routing modes
        """
        # Construct merged leg and mode sequence
        new_pattern = TripPattern(
            legs=(
                (
                   routed_suffix_pattern.originalLegs
                   if routed_suffix_pattern
                   else [] 
                ) + new_legs + base_legs
            ),
            modes=(
                (
                    routed_suffix_pattern.modes
                    if routed_suffix_pattern
                    else []
                ) + self.__ctx.data.modes
            )
        )
        # Set final aimed end time based on last leg
        new_pattern.aimedEndTime = new_pattern.legs[-1].aimedEndTime

        # Legs post-processing
        LegUtils.process_legs(new_pattern)

        return new_pattern
    
    def __merge_with_base_departure(
        self,
        routed_prefix_pattern: TripPattern | None,
        new_legs: List[Leg],
        base_legs: List[Leg]
    ) -> TripPattern:
        """
        Merges rerouted prefix with new legs and preserved base legs.

        Args:
            routed_prefix_pattern: Result of rerouted prefix
            new_legs: Newly constructed legs caused by bike station change
            base_legs: Unaffected suffix of original trip pattern

        Returns:
            Newly constructed TripPattern with merged legs and updated routing modes
        """
        # Construct merged leg and mode sequence
        new_pattern = TripPattern(
            legs=(
                base_legs + new_legs + (
                   routed_prefix_pattern.originalLegs
                   if routed_prefix_pattern
                   else [] 
                )
            ),
            modes=(
                self.__ctx.data.modes + (
                    routed_prefix_pattern.modes
                    if routed_prefix_pattern
                    else []
                )
            )
        )

        # Set final aimed end time based on last leg
        new_pattern.aimedEndTime = new_pattern.legs[-1].aimedEndTime

        # Legs post-processing
        LegUtils.process_legs(new_pattern)

        return new_pattern

    def __justify_segment(
        self,
        new_legs: List[Leg]
    ) -> None:
        """
        Adjusts timing of rebuilt segment.

        Args:
            new_legs: List of legs forming modified segment
        """
        # Normalize timing of segment based on time cursor and routing direction
        PatternUtils.justify_time(
            TripPattern(legs=new_legs),
            self.__ctx.time_cursor,
            self.__routing_ctx.data.arrive_by
        )

    async def __prepare_waypoint_connection_destination_arrival(
        self,
        new_legs: List[Leg],
        leg_index: int,
        waypoint_count: int
    ) -> Tuple[List[str], List[RoutingMode]]:
        """
        Reconnects modified destination station
        to original waypoint structure.

        Args:
            new_legs: Newly built legs for modified segment
            leg_index: Index where rebuild begins
            waypoint_count: Number of waypoints affected by modification

        Returns:
            Tuple (waypoints to be rerouted, routing modes for affected segment)
        """
        legs = self.__ctx.data.original_legs

        # Reconnect modified route to original waypoints
        reconnect_leg_index = leg_index - 2
        from_place = legs[reconnect_leg_index].fromPlace
        to_place = self.__ctx.place

        if not from_place:
            raise HTTPException(
                status_code = 400,
                detail = "FromPlace missing in data"
            )

        # Compute bicycle segment from previous waypoint to new destination station
        bike_pattern = await self.__otp_bicycle_client.execute(
            (from_place.latitude, from_place.longitude),
            (to_place.latitude, to_place.longitude),
        )

        if not bike_pattern:
            raise HTTPException(
                status_code = 400,
                detail = "Bike pattern not found"
            )
    
        # Append bicycle legs before original legs
        new_legs[:0] = bike_pattern[0].legs

        # Skip the bicycle leg
        reconnect_leg_index -= 1

        # Reinsert remaining bicycle legs until foot segment is reached
        while reconnect_leg_index > 0 and legs[reconnect_leg_index].mode != "foot":
            # Adjusts waypoint count
            if legs[reconnect_leg_index].mode == "bicycle":
                waypoint_count -= 1
            new_legs.insert(0, deepcopy(legs[reconnect_leg_index]))
            reconnect_leg_index -= 1
        
        found_waypoint = True
        from_place = legs[reconnect_leg_index].fromPlace

        if not from_place:
            raise HTTPException(
                status_code = 400,
                detail = "FromPlace missing in data"
            )

        # Determine affected waypoints
        waypoint_group = self.__routing_ctx.data.waypoints[:waypoint_count]
        # Get routing modes
        routing_modes = self.__ctx.data.modes[:waypoint_count - 1]

        # Determine if waypoint was reached
        if reconnect_leg_index > 0:
            found_waypoint = self.__at_waypoint(
                from_place.latitude,
                from_place.longitude,
                waypoint_group[-1]
            )
        
        # Append leg if it leads to waypoint
        if found_waypoint:
            new_legs.insert(0, deepcopy(legs[reconnect_leg_index]))
        # Add artificial waypoint when waypoint was not reached
        else:
            to_place = legs[reconnect_leg_index].toPlace
            if not to_place:
                raise HTTPException(
                    status_code = 400,
                    detail = "FromPlace missing in data"
                )
            waypoint_group.append(f"{to_place.latitude}, {to_place.longitude}")
            routing_modes.append("walk_transit")

        return waypoint_group, routing_modes

    async def __prepare_waypoint_connection_destination_departure(
        self,
        new_legs: List[Leg],
        leg_index: int,
        waypoint_count: int
    ) -> Tuple[List[str], List[RoutingMode]]:
        """
        Reconnects modified destination station.

        Args:
            new_legs: Newly built legs
            leg_index: Index where rebuild begins
            waypoint_count: Number of affected waypoints

        Returns:
            Tuple (waypoints to be rerouted, routing modes for affected segment)
        """
        legs = self.__ctx.data.original_legs

        # Reconnect modified route to original waypoints
        reconnect_leg_index = leg_index + 2

        # Get affected waypoints
        waypoint_group = self.__routing_ctx.data.waypoints[-waypoint_count:]

        # Get routing modes
        routing_modes = self.__ctx.data.modes[-waypoint_count+1:] if waypoint_count > 1 else []
        from_place = self.__ctx.place
        to_place = legs[reconnect_leg_index].toPlace

        if not to_place:
            raise HTTPException(
                status_code = 400,
                detail = "ToPlace missing in data"
            )

        waypoint_found = True
        # Determine if waypoint was reached
        if waypoint_group and to_place:
            waypoint_found = self.__at_waypoint(
                to_place.latitude,
                to_place.longitude,
                waypoint_group[0]
            )

        # Compute foot route new bike station to next waypoint
        if waypoint_found:
            walk_patterns = await self.__otp_foot_client.execute(
                (from_place.latitude, from_place.longitude),
                (to_place.latitude, to_place.longitude),
            )
            # Foot pattern not found and the waypoints are too close insert artificial foot leg
            if not walk_patterns and GeoMath.haversine_distance_km(
                from_place.latitude, from_place.longitude,
                to_place.latitude, to_place.longitude
            ) < 0.003:
                new_legs.append(self.__prepare_artificial_leg(from_place, to_place))
            elif not walk_patterns:
                raise HTTPException(
                    status_code = 400,
                    detail = "Foot pattern not found"
                )
            else:
                new_legs.extend(walk_patterns[0].legs)

        # Add artificial waypoint when waypoint was not reached
        else:
            waypoint_group.insert(0, f"{from_place.latitude},{from_place.longitude}")
            routing_modes.insert(0, "walk_transit")

        return waypoint_group, routing_modes

    async def __prepare_waypoint_connection_origin_arrival(
        self,
        new_legs: List[Leg],
        leg_index: int,
        waypoint_count: int
    ) -> Tuple[List[str], List[RoutingMode]]:
        """
        Reconnects modified origin station.

        Args:
            new_legs: Newly built legs
            leg_index: Index where rebuild begins
            waypoint_count: Number of affected waypoints

        Returns:
            Tuple (waypoints to be rerouted, routing modes for affected segment)
        """
        # Get affected waypoints
        waypoint_group = self.__routing_ctx.data.waypoints[:waypoint_count]
        # Get routing modes
        routing_modes = self.__ctx.data.modes[:waypoint_count - 1]

        # Reconnect modified route to original waypoints
        reconnect_leg_index = leg_index - 2
        from_place = self.__ctx.data.original_legs[reconnect_leg_index].fromPlace
        to_place = self.__ctx.place

        waypoint_found = True
        # Determine if waypoint was reached
        if waypoint_group and from_place:
            waypoint_found = self.__at_waypoint(
                from_place.latitude,
                from_place.longitude,
                waypoint_group[-1]
            )

        # Add walking connection from waypoint to bike station
        if waypoint_found and from_place:
            walk_patterns = await self.__otp_foot_client.execute(
                (from_place.latitude, from_place.longitude),
                (to_place.latitude, to_place.longitude),
            )

            # Foot pattern not found and the waypoints are too close insert artificial foot leg
            if not walk_patterns and GeoMath.haversine_distance_km(
                from_place.latitude, from_place.longitude,
                to_place.latitude, to_place.longitude
            ) < 0.003:
                new_legs.insert(0, self.__prepare_artificial_leg(from_place, to_place))
            elif not walk_patterns:
                raise HTTPException(
                    status_code = 400,
                    detail = "Foot pattern not found"
                )
            else:
                # Append foot legs before original legs
                new_legs[:0] = walk_patterns[0].legs

        # Add artificial waypoint when waypoint was not reached
        else:
            waypoint_group.append(f"{to_place.latitude},{to_place.longitude}")
            routing_modes.append("walk_transit")

        return waypoint_group, routing_modes
        
    async def __prepare_waypoint_connection_origin_departure(
        self,
        new_legs: List[Leg],
        leg_index: int,
        waypoint_count: int
    ) -> Tuple[List[str], List[RoutingMode]]:
        """
        Reconnects modified origin segment.

        Args:
            new_legs: Newly built legs
            leg_index: Index where rebuild begins
            waypoint_count: Number of affected waypoints

        Returns:
            Tuple (waypoints to be rerouted, routing modes for affected segment)
        """
        legs = self.__ctx.data.original_legs

        # Reconnect modified route to original waypoints
        reconnect_leg_index = leg_index + 2
        from_place = self.__ctx.place
        to_place = legs[reconnect_leg_index].toPlace

        if not to_place:
            raise HTTPException(
                status_code = 400,
                detail = "ToPlace missing in data"
            )
    
        # Compute route from new origin station to next point
        bike_pattern = await self.__otp_bicycle_client.execute(
            (from_place.latitude, from_place.longitude),
            (to_place.latitude, to_place.longitude),
        )

        if not bike_pattern:
            raise HTTPException(
                status_code = 400,
                detail = "Bike pattern not found"
            )
    
        # Add new legs
        new_legs.extend(bike_pattern[0].legs)

        # Skip the bicycle leg
        reconnect_leg_index += 1

        # Add bicycle remaining legs
        while reconnect_leg_index < len(legs) and legs[reconnect_leg_index].mode != "foot":
            # Adjusts waypoint count
            if legs[reconnect_leg_index].mode == "bicycle":
                waypoint_count -= 1
            new_legs.append(deepcopy(legs[reconnect_leg_index]))
            reconnect_leg_index += 1

        # Get waypoint for which routing is required
        waypoint_group = self.__routing_ctx.data.waypoints[-waypoint_count:]

        # Get routing modes
        routing_modes = (
            self.__ctx.data.modes[-waypoint_count + 1:]
            if waypoint_count > 1 
            else []
        )

        found_waypoint = True
        # Determine if waypoint was reached
        if reconnect_leg_index < len(legs):
            to_place = legs[reconnect_leg_index].toPlace

            if not to_place:
                raise HTTPException(
                    status_code = 400,
                    detail = "ToPlace missing in data"
                )

            found_waypoint = self.__at_waypoint(
                to_place.latitude,
                to_place.longitude,
                waypoint_group[0]
            )

        # Append leg if it leads to waypoint
        if found_waypoint:
            new_legs.append(deepcopy(legs[reconnect_leg_index]))
        # Insert artificial waypoint when waypoint was not reached
        else:
            from_place = legs[reconnect_leg_index].fromPlace

            if not from_place:
                raise HTTPException(
                    status_code = 400,
                    detail = "ToPlace missing in data"
                )

            waypoint_group.insert(0, f"{from_place.latitude}, {from_place.longitude}")
            routing_modes.insert(0, "walk_transit")

        return waypoint_group, routing_modes

    async def __build_station_suffix(
        self,
        leg_index: int
    ) -> List[Leg]:
        """
        Builds suffix segment connecting modified bike station
        to the next original leg.

        Args:
            leg_index: Index of leg in original route used for reconnection

        Returns:
            List of newly computed legs including wait segment.
        """
        from_place = self.__ctx.place
        to_place = self.__ctx.data.original_legs[leg_index].toPlace

        if not to_place:
            raise HTTPException(
                status_code=400,
                detail="ToPlace missing in data"
            )

        # Select OTP client
        otp_client = (
            self.__otp_bicycle_client
            if self.__ctx.data.origin_bike_station
            else self.__otp_foot_client
        )
        
        # Compute route between station and reconnection point
        # Bike pattern if origin station, foot pattern if destination station
        pattern = await otp_client.execute(
            (from_place.latitude, from_place.longitude),
            (to_place.latitude, to_place.longitude)
        )

        if not pattern:
            # Foot pattern not found and the waypoints are too close insert artificial foot leg
            if not self.__ctx.data.origin_bike_station and GeoMath.haversine_distance_km(
                from_place.latitude, from_place.longitude,
                to_place.latitude, to_place.longitude
            ) < 0.003:
                new_legs = [self.__prepare_artificial_leg(from_place, to_place)]
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Pattern not found"
                )
        else:
            # Initialize new legs
            new_legs = pattern[0].legs

        # Insert wait leg
        new_legs.insert(0, self.__prepare_wait_leg())

        return new_legs
    
    async def __build_station_prefix(
        self,
        leg_index: int
    ) -> List[Leg]:
        """
        Builds prefix segment connecting previous original leg
        to modified bike station.

        Args:
            leg_index: Index of leg in original route used for reconnection

        Returns:
            List of newly computed legs including wait segment.
        """
        from_place = self.__ctx.data.original_legs[leg_index].fromPlace
        to_place = self.__ctx.place

        if not from_place:
            raise HTTPException(
                status_code=400,
                detail="FromPlace missing in data"
            )
        
        # Select OTP client
        otp_client = (
            self.__otp_foot_client
            if self.__ctx.data.origin_bike_station
            else self.__otp_bicycle_client
        )

        # Compute route between reconnection point and station
        # Foot pattern if origin station, bike pattern if destination station
        pattern = await otp_client.execute(
            (from_place.latitude, from_place.longitude),
            (to_place.latitude, to_place.longitude)
        )

        if not pattern:
            # Foot pattern not found and the waypoints are too close insert artificial foot leg
            if self.__ctx.data.origin_bike_station and GeoMath.haversine_distance_km(
                from_place.latitude, from_place.longitude,
                to_place.latitude, to_place.longitude
            ) < 0.003:
                new_legs = [self.__prepare_artificial_leg(from_place, to_place)]
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Pattern not found"
                )
        else:
            # Initialize new legs
            new_legs = pattern[0].legs

        # Append wait leg
        new_legs.append(self.__prepare_wait_leg())

        return new_legs

    def __prepare_wait_leg(self) -> Leg:
        """
        Creates artificial wait leg representing bike lock/unlock time.

        Returns:
            Leg instance with mode "wait" and bike station metadata.
        """
        return Leg(
            mode="wait",
            color="black",
            duration=self.__routing_ctx.bike_lock_time * 60,
            pointsOnLink=PointOnLink(
                points=[]
            ),
            bikeStationInfo=BikeStationInfo(
                rack=False,
                latitude=self.__ctx.place.latitude,
                longitude=self.__ctx.place.longitude,
                origin=self.__ctx.data.origin_bike_station,
                selectedBikeStationIndex=self.__ctx.data.new_index,
                bikeStations=self.__ctx.data.bike_stations
            )
        )
    
    @staticmethod
    def __prepare_artificial_leg(from_place: PlaceBase, to_place: PlaceBase) -> Leg:
        """
        Prepare artificial foot leg.

        Args:
            from_place: First place coordinates
            to_place: Second place coordinates

        Returns:
            Prepared artificial leg
        """
        return Leg(
            mode="foot",
            duration=0,
            pointsOnLink=PointOnLink(points=[]),
            fromPlace=Place(
                latitude=from_place.latitude,
                longitude=from_place.longitude
            ),
            toPlace=Place(
                latitude=to_place.latitude,
                longitude=to_place.longitude
            ),
            artificial=True
        )

    def __find_affected_segment_arrival(self) -> Tuple[int, int]:
        """
        Identifies affected segment when rebuilding route.

        Returns:
            Tuple (Index of first leg after affected segment, number of 
            consecutive time-independent segments)
        """
        # Original route legs
        legs = self.__ctx.data.original_legs

        # Start from first leg
        i = 0

        # Count consecutive independent segments
        waypoint_count = 1

        # Track previous mode
        mode: Mode | Literal[""] = ""

        while i < len(legs) - 1 and i < self.__ctx.data.leg_index + 1:        
            # Count consecutive foot/bicycle segments
            if mode == legs[i].mode and mode in TIME_INDEPENDENT_MODES:
                waypoint_count += 1

            mode = legs[i].mode
            i += 1

        return i, waypoint_count

    def __find_affected_segment_departure(self) -> Tuple[int, int]:
        """
        Identifies affected segment when rebuilding route.

        Returns:
            Tuple (index of last unaffected leg, number of consecutive time
            independent segments)
        """
        # Original route legs
        legs = self.__ctx.data.original_legs

        # Start from last leg
        i = len(legs) - 1

        # Count consecutive independent segments
        waypoint_count = 1

        # Track previous mode
        mode: Mode | Literal[""] = ""

        while i >= 0 and i > self.__ctx.data.leg_index - 2: 
            # Count consecutive foot/bicycle segments
            if mode == legs[i].mode and mode in TIME_INDEPENDENT_MODES:
                waypoint_count += 1

            mode = legs[i].mode
            i -= 1

        return i, waypoint_count

    async def __route_changed_part(
        self,
        routing_modes: List[RoutingMode],
        waypoint_group: List[str],
        time_cursor: datetime
    ) -> TripPattern | None:
        """
        Re-routes modified segment of trip after bike station change.

        Args:
            routing_modes: Transport modes for affected segment
            waypoint_group: Waypoints defining affected part to recompute
            time_cursor: Reference time for rerouting

        Returns:
            First TripPattern returned by routing engine,
            or None if no route was found.
        """
        # Offset for mapping station indices for the changed route part
        offset = (
            len(self.__routing_ctx.data.waypoints) - len(waypoint_group)
            if not self.__routing_ctx.data.arrive_by
            else 0
        )

        origin_station = self.__routing_ctx.data.origin_station
        if origin_station is not None:
            origin_station.index -= offset

        destination_station = self.__routing_ctx.data.destination_station
        if destination_station is not None:
            destination_station.index -= offset

        # Create modified RouteData for partial rerouting
        new_route_data = self.__routing_ctx.data.model_copy(
            update={
                "leg_preferences": [
                    LegPreferences(mode=mode, wait=0)
                    for mode in routing_modes
                ],
                "waypoints": waypoint_group,
                "date": time_cursor.date(),
                "time": time_cursor.time(),
                "origin_station": origin_station,
                "destination_station": destination_station
            }
        )

        # Initialize routing engine with updated data
        engine = RoutingEngine(new_route_data, self.__routing_ctx.session)

        # Execute routing
        trip_patterns = await engine.plan_route()
        
        # Return first pattern if available
        return trip_patterns[0] if trip_patterns else None

    @staticmethod
    def __at_waypoint(lat: float, lon: float, waypoint: str) -> bool:
        """
        Check whether a given geographic position is close a specified waypoint

        Args:
            lat: Latitude of the given position
            lon: Longitude of the given position
            waypoint: Waypoint coordinates in format lat,lon
        
        Returns:
            True, if the position is within 50 meters of the waypoint, false otherwise
        """
        # Get waypoint coordinates
        waypoint_lat, waypoint_lon = map(float, waypoint.split(','))

        # Compute distance in meters
        distance_m = GeoMath.haversine_distance_km(lat, lon, waypoint_lat, waypoint_lon) * 1000

        return distance_m < 50

    def __normalize_modes(self, modes: List[RoutingMode]) -> List[RoutingMode]:
        """
        Normalizes routing modes for partial rerouting.

        Ensures hybrid modes are converted to walk_transit
        depending on routing direction.

        Args:
            modes: Original routing modes for affected segment

        Returns:
            List of normalized routing modes.
        """
        if self.__routing_ctx.data.arrive_by:
            # Remove public_bicycle from routing modes
            return [
                mode 
                if mode != "public_bicycle" 
                else "walk_transit"
                for mode in modes
            ]
        else:
            # Remove bicycle_public from routing modes
            return [
                mode 
                if mode != "bicycle_public" 
                else "walk_transit"
                for mode in modes
            ]
       
# End of file station_changer.py
