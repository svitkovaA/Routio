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
from models.route import TIME_INDEPENDENT_MODES, BikeStationInfo, Leg, Mode, PointOnLink, RoutingMode, TripPattern
from routing_engine.routing_context import RoutingContext
from models.bike_station_data import BikeStationData

class StationChanger():
    def __init__(self, data: BikeStationData,  session: AsyncClientSession):
        self.__routing_ctx = RoutingContext(data.route_data, session)
        self.__ctx = StationChangerContext(data)
        self.__otp_bicycle_client = OTPBicycle(self.__routing_ctx)
        self.__otp_foot_client = OTPFoot(self.__routing_ctx)

    async def change_bike_station(self) -> TripPattern:
        if self.__routing_ctx.data.arrive_by:
            return await self.__rebuild_pattern_arrival()
        else:
            return await self.__rebuild_pattern_departure()

    async def __rebuild_pattern_departure(self) -> TripPattern:
        legs = self.__ctx.data.original_legs

        leg_index, waypoint_count = self.__find_affected_segment_departure()

        # Preserve unaffected prefix of the original route
        base_legs = deepcopy(legs[:leg_index+1])
        leg_index = len(base_legs)

        new_legs = await self.__build_station_prefix(leg_index)

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

        self.__justify_segment(new_legs)

        rerouted_prefix_pattern = await self.__route_changed_part(
            normalized_routing_modes,
            waypoint_group,
            new_legs[-1].aimedEndTime
        )

        return self.__merge_with_base_departure(
            rerouted_prefix_pattern,
            new_legs,
            base_legs
        )

    async def __rebuild_pattern_arrival(self) -> TripPattern:
        legs = self.__ctx.data.original_legs

        leg_index, waypoint_count = self.__find_affected_segment_arrival()

        # Preserve unaffected suffix of the original route
        base_legs = deepcopy(legs[leg_index + 1:])
        leg_index = len(legs) - len(base_legs) - 1

        new_legs = await self.__build_station_suffix(leg_index)

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

        self.__justify_segment(new_legs)

        rerouted_prefix_pattern = await self.__route_changed_part(
            normalized_routing_modes,
            waypoint_group,
            new_legs[0].aimedStartTime
        )

        return self.__merge_with_base_arrival(
            rerouted_prefix_pattern,
            new_legs,
            base_legs
        )

    def __merge_with_base_arrival(
        self,
        routed_prefix_pattern: TripPattern | None,
        new_legs: List[Leg],
        base_legs: List[Leg]
    ) -> TripPattern:
        new_pattern = TripPattern(
            legs=(
                (
                   routed_prefix_pattern.legs
                   if routed_prefix_pattern
                   else [] 
                ) + new_legs + base_legs
            ),
            modes=(
                (
                    routed_prefix_pattern.modes
                    if routed_prefix_pattern
                    else []
                ) + self.__ctx.data.modes
            )
        )
        new_pattern.aimedEndTime = new_pattern.legs[-1].aimedEndTime

        LegUtils.process_legs(new_pattern)

        return new_pattern
    
    def __merge_with_base_departure(
        self,
        routed_prefix_pattern: TripPattern | None,
        new_legs: List[Leg],
        base_legs: List[Leg]
    ) -> TripPattern:
        new_pattern = TripPattern(
            legs=(
                base_legs + new_legs + (
                   routed_prefix_pattern.legs
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

        new_pattern.aimedEndTime = new_pattern.legs[-1].aimedEndTime

        LegUtils.process_legs(new_pattern)

        return new_pattern

    def __justify_segment(
        self,
        new_legs: List[Leg]
    ) -> None:
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
        legs = self.__ctx.data.original_legs

        reconnect_leg_index = leg_index - 2
        from_place = legs[reconnect_leg_index].fromPlace
        to_place = self.__ctx.place

        if not from_place:
            raise HTTPException(
                status_code = 400,
                detail = "FromPlace missing in data"
            )

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

        waypoint_group = self.__routing_ctx.data.waypoints[:waypoint_count]
        routing_modes = self.__ctx.data.modes[:waypoint_count - 1]

        if reconnect_leg_index > 0:
            found_waypoint = self.__at_waypoint(
                from_place.latitude,
                from_place.longitude,
                waypoint_group[-1]
            )
        
        if found_waypoint:
            new_legs.insert(0, deepcopy(legs[reconnect_leg_index]))
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
        reconnect_leg_index = leg_index + 2
        legs = self.__ctx.data.original_legs

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
        if waypoint_group and to_place:
            waypoint_found = self.__at_waypoint(
                to_place.latitude,
                to_place.longitude,
                waypoint_group[0]
            )

        if waypoint_found:
            walk_patterns = await self.__otp_foot_client.execute(
                (from_place.latitude, from_place.longitude),
                (to_place.latitude, to_place.longitude),
            )
            if not walk_patterns:
                raise HTTPException(
                    status_code = 400,
                    detail = "Foot pattern not found"
                )
            new_legs.extend(walk_patterns[0].legs)
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
        waypoint_group = self.__routing_ctx.data.waypoints[:waypoint_count]
        routing_modes = self.__ctx.data.modes[:waypoint_count - 1]

        reconnect_leg_index = leg_index - 2
        from_place = self.__ctx.place
        to_place = self.__ctx.data.original_legs[reconnect_leg_index].fromPlace

        waypoint_found = True

        if waypoint_group and to_place:
            waypoint_found = self.__at_waypoint(
                to_place.latitude,
                to_place.longitude,
                waypoint_group[-1]
            )

        if waypoint_found and to_place:
            walk_patterns = await self.__otp_foot_client.execute(
                (from_place.latitude, from_place.longitude),
                (to_place.latitude, to_place.longitude),
            )
            if not walk_patterns:
                raise HTTPException(
                    status_code = 400,
                    detail = "Foot pattern not found"
                )
            new_legs[:0] = walk_patterns[0].legs
        else:
            waypoint_group.append(f"{from_place.latitude},{from_place.longitude}")
            routing_modes.append("walk_transit")

        return waypoint_group, routing_modes
        
    async def __prepare_waypoint_connection_origin_departure(
        self,
        new_legs: List[Leg],
        leg_index: int,
        waypoint_count: int
    ) -> Tuple[List[str], List[RoutingMode]]:
        reconnect_leg_index = leg_index + 2
        legs = self.__ctx.data.original_legs
        from_place = self.__ctx.place
        to_place = legs[reconnect_leg_index].toPlace

        if not to_place:
            raise HTTPException(
                status_code = 400,
                detail = "ToPlace missing in data"
            )
    
        bike_pattern = await self.__otp_bicycle_client.execute(
            (from_place.latitude, from_place.longitude),
            (to_place.latitude, to_place.longitude),
        )

        if not bike_pattern:
            raise HTTPException(
                status_code = 400,
                detail = "Bike pattern not found"
            )
    
        new_legs.extend(bike_pattern[0].legs)

        # Skip the bicycle leg
        reconnect_leg_index += 1

        while reconnect_leg_index < len(legs) and legs[reconnect_leg_index].mode != "foot":
            if legs[reconnect_leg_index].mode == "bicycle":
                waypoint_count -= 1
            new_legs.append(deepcopy(legs[reconnect_leg_index]))
            reconnect_leg_index += 1

        # Determine if waypoint was reached
        found_waypoint = True
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
                self.__routing_ctx.data.waypoints[waypoint_count - 1]
            )

        # Get waypoint for which routing is required
        waypoint_group = self.__routing_ctx.data.waypoints[-waypoint_count:]

        # Get routing modes for part of trip to recalculate
        routing_modes = (
            self.__ctx.data.modes[-waypoint_count + 1:]
            if waypoint_count > 1 
            else []
        )

        if found_waypoint:
            new_legs.append(deepcopy(legs[reconnect_leg_index]))
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
        from_place = self.__ctx.place
        to_place = self.__ctx.data.original_legs[leg_index].toPlace

        if not to_place:
            raise HTTPException(
                status_code=400,
                detail="ToPlace missing in data"
            )

        otp_client = (
            self.__otp_bicycle_client
            if self.__ctx.data.origin_bike_station
            else self.__otp_foot_client
        )
        
        # Bike pattern if origin station, foot pattern if destination station
        pattern = await otp_client.execute(
            (from_place.latitude, from_place.longitude),
            (to_place.latitude, to_place.longitude)
        )

        if not pattern:
            raise HTTPException(
                status_code=400,
                detail="Pattern not found"
            )

        # Initialize new legs
        new_legs = pattern[0].legs

        # Insert wait leg (bike lock)
        new_legs.insert(0, self.__prepare_wait_leg())

        return new_legs
    
    async def __build_station_prefix(
        self,
        leg_index: int
    ) -> List[Leg]:
        from_place = self.__ctx.data.original_legs[leg_index].fromPlace
        to_place = self.__ctx.place

        if not from_place:
            raise HTTPException(
                status_code=400,
                detail="FromPlace missing in data"
            )
        
        otp_client = (
            self.__otp_foot_client
            if self.__ctx.data.origin_bike_station
            else self.__otp_bicycle_client
        )

        # Foot pattern if origin station, bike pattern if destination station
        pattern = await otp_client.execute(
            (from_place.latitude, from_place.longitude),
            (to_place.latitude, to_place.longitude)
        )

        if not pattern:
            raise HTTPException(
                status_code=400,
                detail="Pattern not found"
            )

        # Initialize new legs
        new_legs = pattern[0].legs

        # Insert wait leg (bike lock)
        new_legs.append(self.__prepare_wait_leg())

        return new_legs

    def __prepare_wait_leg(self) -> Leg:
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
    
    def __find_affected_segment_arrival(self) -> Tuple[int, int]:
        legs = self.__ctx.data.original_legs
        compressed_legs = self.__ctx.compressed_legs

        i = 0
        compressed_index = 0
        waypoint_count = 1
        mode: Mode | Literal[""] = ""

        # Find the first leg affected by the bike station change
        while i < len(legs) - 1 and compressed_index < len(compressed_legs) - 1:
            if legs[i].mode == compressed_legs[compressed_index].mode:
                compressed_index += 1
            
            # Count consecutive foot/bicycle segments
            if mode == legs[i].mode and mode in TIME_INDEPENDENT_MODES:
                waypoint_count += 1

            mode = legs[i].mode
            i += 1

        return i, waypoint_count

    def __find_affected_segment_departure(self) -> Tuple[int, int]:
        legs = self.__ctx.data.original_legs
        compressed_legs = self.__ctx.compressed_legs

        i = len(legs) - 1
        compressed_index = len(compressed_legs) - 1
        waypoint_count = 1
        mode: Mode | Literal[""] = ""

        while i >= 0 and compressed_index >= 0:
            if legs[i].mode == compressed_legs[compressed_index].mode:
                compressed_index -= 1
            
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
        new_route_data = self.__routing_ctx.data.model_copy(
            update={
                "leg_preferences": [
                    LegPreferences(mode=mode, wait=0)
                    for mode in routing_modes
                ],
                "waypoints": waypoint_group,
                "date": time_cursor.date(),
                "time": time_cursor.time()
            }
        )

        engine = RoutingEngine(new_route_data, self.__routing_ctx.session)
        trip_patterns = await engine.plan_route()
        
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
        if self.__routing_ctx.data.arrive_by:
            return [
                mode 
                if mode != "public_bicycle" 
                else "walk_transit"
                for mode in modes
            ]
        else:
            return [
                mode 
                if mode != "bicycle_public" 
                else "walk_transit"
                for mode in modes
            ]
       