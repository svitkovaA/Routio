"""
file: own_bicycle_router.py

wn bicycle routers implementation. This file implements routing logic for
routes using own bicycles. It combines bicycle rack near the destination, 
computes cycling segments, inserts lock time wait leg, and optionally adds
a final walking segment.
"""

from typing import List
from routing_engine.routing_context import RoutingContext
from routers.bicycles.bicycle_router_base import BicycleRouterBase
from shared.pattern_utils import PatternUtils
from routers.bicycles.own_bicycle.bike_rack_selector import BikeRackSelector
from models.route import BikeRackNode, BikeStationInfo, Leg, PointOnLink, TripPattern
from models.planning_context import PlanningContext

class OwnBicycleRouter(BicycleRouterBase):
    """
    Concrete bicycle router for users riding their own bicycle.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes own bicycle router.

        Args:
            context: Global routing context containing configuration
        """
        # Initialize base router context
        super().__init__(context)

        # Station selector used to rank candidate bicycle racks
        self.__bike_rack_selector = BikeRackSelector()

    async def route_bike_group(self, context: PlanningContext) -> List[TripPattern]:
        """
        Main entry point for own bicycle routing. Selects bicycle rack
        alternatives, computes walking and cycling segments, and builds all
        valid trip combinations.

        Args:
            context: Planning context containing waypoints and routing flags

        Returns:
            List with trip pattern
        """
        # Select candidate racks near destination
        sorted_racks = await self.__bike_rack_selector.select_racks(
            context.bicycle_public,
            self._parse_coordinates(context.waypoints[-2]),
            self._parse_coordinates(context.waypoints[-1])
        )

        # Abort if no rack available
        if not sorted_racks:
            return []
        
        # Compute cycling segments between waypoints
        base_trip_patterns = await self._route_bicycle_segments(context.waypoints[:-1])

        # Use best ranked rack
        rack = sorted_racks[0]

        # Extend route to selected rack
        trip_pattern = await self.__route_to_bike_rack(
            base_trip_patterns,
            rack,
            context.waypoints[0]
        )

        # Abort if extension failed
        if not trip_pattern:
            return []

        # Prepare and insert lock time leg
        wait_leg = self.__prepare_wait_leg(sorted_racks)
        trip_pattern.legs.append(wait_leg)

        # Optionally append walking segment from rack to destination
        if not context.bicycle_public:
            walk_route = await self._otp_foot_client.execute(
                (rack.place.latitude, rack.place.longitude),
                self._parse_coordinates(context.waypoints[-1])
            )

            trip_pattern.legs.extend(walk_route[0].legs)

        # Adjust timing across legs
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
        """
        Extends cycling route to selected bicycle rack.

        Args:
            base_trip_patterns: Previously computed cycling patterns
            rack: Selected bike rack node
            origin: Original starting coordinate

        Returns:
            Extended trip patterns
        """
        # Routing between more than 2 waypoints
        if len(base_trip_patterns) > 0:
            pattern = base_trip_patterns[0]

            # Ensure last segment has valid endpoint
            if not pattern.legs[-1].toPlace:
                return None
            
            # Route from last cycling endpoint to rack
            bike_route = await self._route_bicycle_segments(
                [
                    f"{pattern.legs[-1].toPlace.latitude}, {pattern.legs[-1].toPlace.longitude}",
                    f"{rack.place.latitude}, {rack.place.longitude}"
                ]
            )

            # Bike route not found
            if not bike_route:
                return None

            # Append rack extension legs
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

            # Bike route not found
            if not bike_route:
                return None

            return bike_route[0]

    def __prepare_wait_leg(self, racks: List[BikeRackNode]) -> Leg:
        """
        Creates wait leg representing bike lock time at rack.

        Args:
            racks: Ranked list of racks

        Returns:
            Leg object with data
        """
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
    
# End of file own_bicycle_router.py
