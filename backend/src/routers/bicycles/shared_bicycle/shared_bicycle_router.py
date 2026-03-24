"""
file: shared_bicycle_router.py

Shared bicycle router implementation. This file implements routing logic for
routes using sharing bicycles. It combines station selection, walking segments,
cycling segments, and station wait times into complete trip patterns.
"""

import asyncio
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from shared.pattern_utils import PatternUtils
from routing_engine.routing_context import RoutingContext
from routers.bicycles.shared_bicycle.bike_station_selector import BikeStationSelector
from routers.bicycles.bicycle_router_base import BicycleRouterBase
from models.route import BikeStationInfo, BikeStationNode, Leg, Place, PointOnLink, TripPattern
from models.planning_context import PlanningContext

@dataclass
class TripContext:
    """
    Aggregated context required to construct a single sharing bicycle trip variant.
    """
    context: PlanningContext
    origin_node: BikeStationNode
    origin_index: int
    destination_node: BikeStationNode
    destination_index: int
    walk_to_origin_map: Dict[str, List[TripPattern]]
    walk_from_destination_map: Dict[str, List[TripPattern]]
    intermediate_legs: List[Leg]
    origin_nodes: List[BikeStationNode]
    destination_nodes: List[BikeStationNode]

class SharedBicycleRouter(BicycleRouterBase):
    """
    Concrete bicycle router for routes using shared bicycle.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes shared bicycle router.

        Args:
            context: Global routing context with configuration
        """
        # Initialize base router context
        super().__init__(context)

        # Station selector used to rank candidate bicycle stations
        self.__bike_station_selector = BikeStationSelector(self._ctx)

    async def route_bike_group(self, context: PlanningContext) -> List[TripPattern]:
        """
        Main entry point for shared bicycle routing. Selects station
        alternatives, computes walking and cycling segments, and builds all
        valid trip combinations.

        Args:
            context: Planning context containing waypoints

        Returns:
            List of valid trip patterns
        """
        # Determine number of station alternatives to evaluate
        num_of_nodes = 1 if self._ctx.data.mode == "multimodal" else 2

        origin_bisector: np.ndarray | None = None
        destination_bisector: np.ndarray | None = None
        if context.use_bisector:
            if len(context.waypoints) >= 3:
                # Compute origin bisector
                if context.public_bicycle:
                    origin_bisector = self._compute_bisector(
                        self._parse_coordinates(context.waypoints[2]),
                        self._parse_coordinates(context.waypoints[1]),
                        self._parse_coordinates(context.waypoints[0])
                    )

                # Compute destination bisector
                if context.bicycle_public:
                    destination_bisector = self._compute_bisector(
                        self._parse_coordinates(context.waypoints[-3]),
                        self._parse_coordinates(context.waypoints[-2]),
                        self._parse_coordinates(context.waypoints[-1])
                    )

        # Retrieve best origin and destination bike stations
        sorted_origin_nodes, sorted_destination_nodes = await asyncio.gather(
            self.__bike_station_selector.select_origin_stations(
                self._parse_coordinates(context.waypoints[0]),  # Trip start
                self._parse_coordinates(context.waypoints[1]),  # Next waypoint
                context,
                origin_bisector
            ),
            self.__bike_station_selector.select_destination_stations(
                self._parse_coordinates(context.waypoints[-2]), # Previous waypoint
                self._parse_coordinates(context.waypoints[-1]), # Trip end
                context,
                destination_bisector
            )
        )

        # Abort early if no viable station alternatives were found
        if not sorted_origin_nodes or not sorted_destination_nodes:
            return []

        # Compute intermediate cycling and walking segments
        intermediate_patterns, walk_to_origin_map, walk_from_destination_map = await asyncio.gather(
            self._route_bicycle_segments(
                context.waypoints[1:-2]                             # Ignore last waypoint
                if context.use_bisector and context.bicycle_public
                else context.waypoints[2:-1]                        # Ignore first waypoint
                if context.use_bisector and context.public_bicycle
                else context.waypoints[1:-1]
            ),  # Middle cycling segments
            self.__route_walk_to_origin_stations(
                sorted_origin_nodes[:num_of_nodes],                 # Candidate origin stations
                self._parse_coordinates(context.waypoints[0]),      # Trip origin
                context
            ),
            self.__route_walk_from_destination_stations(
                sorted_destination_nodes[:num_of_nodes],            # Candidate destination stations
                self._parse_coordinates(context.waypoints[-1]),     # Trip destination
                context
            ),
        )
        
        # Flatten intermediate cycling patterns into a single leg list
        intermediate_legs = [
            leg 
            for pattern in intermediate_patterns
            for leg in pattern.legs
        ]
        
        # Create asynchronous build tasks for each station combination
        trip_tasks = [
            self.__build_trip(TripContext(
                context=context,
                origin_node=origin_node,
                origin_index=origin_index,
                destination_node=destination_node,
                destination_index=destination_index,
                walk_to_origin_map=walk_to_origin_map,
                walk_from_destination_map=walk_from_destination_map,
                intermediate_legs=intermediate_legs,
                origin_nodes=sorted_origin_nodes,
                destination_nodes=sorted_destination_nodes
            ))
            for origin_index, origin_node in enumerate(sorted_origin_nodes[:num_of_nodes])
            for destination_index, destination_node in enumerate(sorted_destination_nodes[:num_of_nodes])
        ]
        
        possible_patterns = await asyncio.gather(*trip_tasks)

        # Return only successfully built patterns
        return [
            pattern
            for pattern in possible_patterns
            if pattern
        ]
    
    async def __route_walk_to_origin_stations(
        self,
        nodes: List[BikeStationNode],
        origin: Tuple[float, float],
        context: PlanningContext
    ) -> Dict[str, List[TripPattern]]:
        """
        Routes walking segments from trip origin to candidate bike stations.

        Args:
            nodes: List of candidate origin bike station nodes to evaluate
            origin: Geographic coordinates of the trip start
            context: Planning context containing

        Returns:
            Mapping station_id to walking trip patterns
        """
        # Skip walking segment for public_bicycle mode
        if context.public_bicycle:
            return {}
        else:
            # Build walking tasks to origin stations
            tasks = {
                node.place.id: self._otp_foot_client.execute(
                    origin,                                     # Trip origin
                    (node.place.latitude, node.place.longitude) # Station location
                )
                for node in nodes
            }

            results = await asyncio.gather(*tasks.values())

            # Maps station id to walking patterns
            return dict(zip(tasks.keys(), results))

    async def __route_walk_from_destination_stations(
        self,
        nodes: List[BikeStationNode],
        destination: Tuple[float, float],
        context: PlanningContext
    ) -> Dict[str, List[TripPattern]]:
        """
        Routes walking segments from candidate bike stations to final destination

        Args:
            nodes: List of candidate destination bike station nodes to evaluate
            destination: Geographic coordinates of the trip end
            context: Planning context containing

        Returns:
            Mapping station_id to walking trip patterns
        """
        # Skip walking segment for bicycle_public mode
        if context.bicycle_public:
            return {}
        else:
            # Build walking tasks from destination stations
            tasks = {
                node.place.id: self._otp_foot_client.execute(
                    (node.place.latitude, node.place.longitude),    # Station location
                    destination                                     # Final destination
                )
                for node in nodes
            }

            results = await asyncio.gather(*tasks.values())

            # Maps station_id to walking patterns
            return dict(zip(tasks.keys(), results))

    async def __build_trip(
        self,
        trip_context: TripContext
    ) -> TripPattern | None:
        """
        Builds a single shared bicycle trip variant.

        Args:
            trip_context: Aggregated context containing

        Returns:
            Fully computed trip pattern
        """
        # Prepare station coordinates
        origin_bike_station = self.__station_coordinates_str(trip_context.origin_node)
        destination_bike_station = self.__station_coordinates_str(trip_context.destination_node)

        # Initialize trip pattern
        if trip_context.context.public_bicycle:
            trip_pattern = TripPattern(legs=[])
        else:
            # Start with walking leg to origin station
            walk_patterns = trip_context.walk_to_origin_map[trip_context.origin_node.place.id]
            
            if not walk_patterns:
                # Append artificial leg if needed
                if trip_context.context.origin_station_id is not None:
                    trip_pattern = TripPattern(legs=[
                    self.__prepare_artificial_leg(trip_context.origin_node)
                ])
                # Abort if walking route not available
                else:
                    return None
            else:
                # Start trip with walking leg
                trip_pattern = deepcopy(walk_patterns[0])
        
        # Compute first cycling segment
        if (len(trip_context.context.waypoints) > 2 and (
            not trip_context.context.use_bisector or (
                trip_context.context.bicycle_public and
                len(trip_context.context.waypoints) > 3
            ) or (
                trip_context.context.public_bicycle and
                not trip_context.origin_node.in_A_plane and
                len(trip_context.context.waypoints) > 3
            )
        )):
            result = await self._route_bicycle_segments([
                origin_bike_station,
                trip_context.context.waypoints[1]
            ])

        elif (
            trip_context.context.public_bicycle and
            trip_context.context.use_bisector and
            trip_context.origin_node.in_A_plane and
            len(trip_context.context.waypoints) > 3
        ):
            result = await self._route_bicycle_segments([
                origin_bike_station,
                trip_context.context.waypoints[2]
            ])

        else:
            result = await self._route_bicycle_segments([
                origin_bike_station,
                destination_bike_station
            ])
        
        # Abort if cycling route failed
        if not result:
            return None
        
        # Validate first cycling leg
        if not result[0].legs or not result[0].legs[0].fromPlace:
            return None

        # Insert bike unlock wait leg
        trip_pattern.legs.append(self.__create_station_wait_leg(
            result[0].legs[0].fromPlace,
            True,
            trip_context.origin_index,
            trip_context.origin_nodes
        ))

        # Append cycling and intermediate legs
        trip_pattern.legs.extend(result[0].legs)
        trip_pattern.legs.extend(trip_context.intermediate_legs)

        # Compute final cycling segment if multiple waypoints exist
        if (len(trip_context.context.waypoints) > 2 and (
            not trip_context.context.use_bisector or (
                trip_context.context.bicycle_public and
                not trip_context.destination_node.in_A_plane and
                len(trip_context.context.waypoints) > 3
            ) or (
                trip_context.context.public_bicycle and
                len(trip_context.context.waypoints) > 3
            )
        )):
            result = await self._route_bicycle_segments([
                trip_context.context.waypoints[-2],
                destination_bike_station
            ])

            # Abort if final cycling route failed
            if not result:
                return None

            # Append final cycling legs
            trip_pattern.legs.extend(result[0].legs)
        elif (
            trip_context.context.bicycle_public and
            trip_context.context.use_bisector and
            trip_context.destination_node.in_A_plane
            and len(trip_context.context.waypoints) > 3
        ):
            result = await self._route_bicycle_segments([
                trip_context.context.waypoints[-3],
                destination_bike_station
            ])

            # Abort if final cycling route failed
            if not result:
                return None

            # Append final cycling legs
            trip_pattern.legs.extend(result[0].legs)
        
        # Validate final cycling leg
        if not result[0].legs or not result[0].legs[-1].toPlace:
            return None

        # Insert bike lock wait leg
        trip_pattern.legs.append(self.__create_station_wait_leg(
            result[0].legs[-1].toPlace,
            False,
            trip_context.destination_index,
            trip_context.destination_nodes
        ))

        # Append final walking segment from destination station if needed
        if not trip_context.context.bicycle_public:
            walk_patterns = trip_context.walk_from_destination_map[trip_context.destination_node.place.id]

            if not walk_patterns:
                # Append artificial leg if needed
                if trip_context.context.destination_station_id is not None:
                    trip_pattern.legs.append(
                    self.__prepare_artificial_leg(trip_context.destination_node)
                )
                # Abort if walking route not available
                else:
                    return None
            else:
                trip_pattern.legs.extend(walk_patterns[0].legs)

        # Adjust trip timing
        PatternUtils.justify_time(
            trip_pattern,
            trip_context.context.time_cursor,
            self._ctx.data.arrive_by
        )

        # Set final aimed end time on last leg
        trip_pattern.aimedEndTime = trip_pattern.legs[-1].aimedEndTime

        return trip_pattern
    
    def __station_coordinates_str(self, node: BikeStationNode) -> str:
        """
        Converts bike station coordinates into string format.

        Args:
            node: Bike station node

        Returns:
            String formatted as latitude, longitude
        """
        return f"{node.place.latitude}, {node.place.longitude}"

    def __create_station_wait_leg(
        self,
        place: Place,
        origin: bool,
        selected_index: int,
        stations: List[BikeStationNode],
    ) -> Leg:
        """
        Creates a wait leg representing bike unlock or lock time.

        Args:
            place: Station location where wait occurs
            origin: True if unlock, origin station, false if lock, destination
            selected_index: Index of selected station in ranked list
            stations: Full list of ranked stations

        Returns:
            Wait leg object
        """
        # Create wait leg for bike unlock/lock time
        leg = self.__prepare_wait_leg()

        # Ensure bike station info exists
        assert leg.bikeStationInfo is not None

        leg.bikeStationInfo.latitude = place.latitude
        leg.bikeStationInfo.longitude = place.longitude
        leg.bikeStationInfo.origin = origin
        leg.bikeStationInfo.selectedBikeStationIndex = selected_index
        leg.bikeStationInfo.bikeStations = stations
        return leg

    @staticmethod
    def __prepare_artificial_leg(node: BikeStationNode) -> Leg:
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
                latitude=node.place.latitude,
                longitude=node.place.longitude
            ),
            toPlace=Place(
                latitude=node.place.latitude,
                longitude=node.place.longitude
            ),
            artificial=True
        )

    def __prepare_wait_leg(self):
        """
        Prepares base wait leg template with default bike station information.

        Returns:
            Leg as wait segment with default values
        """
        return Leg(
            mode="wait",
            color="black",
            duration=self._ctx.bike_lock_time * 60,
            pointsOnLink=PointOnLink(
                points=[]
            ),
            bikeStationInfo=BikeStationInfo(
                rack=False,
                latitude=0,                 # Dummy value
                longitude=0,                # Dummy value
                origin=True,
                selectedBikeStationIndex=-1,
                bikeStations=[]
            )
        )

# End of file shared_bicycle_router.py
