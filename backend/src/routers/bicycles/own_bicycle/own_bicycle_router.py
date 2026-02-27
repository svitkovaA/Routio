from typing import List
from routing_engine.routing_context import RoutingContext
from routers.bicycles.bicycle_router_base import BicycleRouterBase
from shared.pattern_utils import PatternUtils
from routers.bicycles.own_bicycle.bike_rack_selector import BikeRackSelector
from models.route import BikeRackNode, BikeStationInfo, Leg, PointOnLink, TripPattern
from models.planning_context import PlanningContext

class OwnBicycleRouter(BicycleRouterBase):
    def __init__(self, context: RoutingContext):
        super().__init__(context)
        self.__bike_rack_selector = BikeRackSelector()

    async def route_bike_group(self, context: PlanningContext) -> List[TripPattern]:
        # Find optimal bicycle rack
        sorted_racks = await self.__bike_rack_selector.select_racks(
            context.bicycle_public,
            self._parse_coordinates(context.waypoints[-2]),
            self._parse_coordinates(context.waypoints[-1])
        )

        # No bicycle rack found
        if not sorted_racks:
            return []
        
        base_trip_patterns = await self._route_bicycle_segments(context.waypoints[:-1])

        # Only best rack is used
        rack = sorted_racks[0]

        trip_pattern = await self.__route_to_bike_rack(
            base_trip_patterns,
            rack,
            context.waypoints[0]
        )

        if not trip_pattern:
            return []

        # Prepare lock time leg
        wait_leg = self.__prepare_wait_leg(sorted_racks)

        # Insert lock time leg
        trip_pattern.legs.append(wait_leg)

        # Optional walking segment to destination
        if not context.bicycle_public:
            walk_route = await self._otp_foot_client.execute(
                (rack.place.latitude, rack.place.longitude),
                self._parse_coordinates(context.waypoints[-1])
            )

            trip_pattern.legs.extend(walk_route[0].legs)

        PatternUtils.justify_time(
            trip_pattern,
            context.time_cursor,
            self._ctx.data.arrive_by
        )
        
        return [trip_pattern]

    async def __route_to_bike_rack(
        self,
        base_trip_patterns: List[TripPattern],
        rack: BikeRackNode,
        origin: str
    ) -> TripPattern | None:
        # Routing between more than 2 waypoints
        if len(base_trip_patterns) > 0:
            pattern = base_trip_patterns[0]

            if not pattern.legs[-1].toPlace:
                return None
            
            # Extend cycling route from last segment endpoint to rack
            bike_route = await self._route_bicycle_segments(
                [
                    f"{pattern.legs[-1].toPlace.latitude}, {pattern.legs[-1].toPlace.longitude}",
                    f"{rack.place.latitude}, {rack.place.longitude}"
                ]
            )

            pattern.legs.extend(bike_route[0].legs)
            return pattern
        
        # Routing between 2 waypoints
        else:
            bike_route = await self._route_bicycle_segments(
                [
                    origin,
                    f"{rack.place.latitude}, {rack.place.longitude}"
                ]
            )

            return bike_route[0]

    def __prepare_wait_leg(self, racks: List[BikeRackNode]) -> Leg:
        # Prepare lock time leg
        return Leg(
            mode="wait",
            color="black",
            duration=self._ctx.bike_lock_time * 60,
            pointsOnLink=PointOnLink(
                points=[]
            ),
            bikeStationInfo=BikeStationInfo(
                rack=True,
                latitude=racks[0].place.latitude,
                longitude=racks[0].place.longitude,
                origin=False,
                selectedBikeStationIndex=0,
                bikeStations=racks
            )
        )
