import asyncio
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Tuple
from shared.pattern_utils import PatternUtils
from routing_engine.routing_context import RoutingContext
from routers.bicycles.shared_bicycle.bike_station_selector import BikeStationSelector
from routers.bicycles.bicycle_router_base import BicycleRouterBase
from models.route import BikeStationInfo, BikeStationNode, Leg, Place, PointOnLink, TripPattern
from models.planning_context import PlanningContext

@dataclass
class TripContext:
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
    def __init__(self, context: RoutingContext):
        super().__init__(context)
        self.__bike_station_selector = BikeStationSelector(self._ctx)

    async def route_bike_group(self, context: PlanningContext) -> List[TripPattern]:
        # Determine number of station alternatives to evaluate
        num_of_nodes = 1 if self._ctx.data.mode == "multimodal" else 2

        # Retrieve best origin and destination bike stations
        sorted_origin_nodes, sorted_destination_nodes = await asyncio.gather(
            self.__bike_station_selector.select_origin_stations(
                self._parse_coordinates(context.waypoints[0]),
                self._parse_coordinates(context.waypoints[1]),
                context
            ),
            self.__bike_station_selector.select_destination_stations(
                self._parse_coordinates(context.waypoints[-2]),
                self._parse_coordinates(context.waypoints[-1]),
                context
            )
        )

        # Abort if no station alternatives found
        if not sorted_origin_nodes or not sorted_destination_nodes:
            return []

        # Compute intermediate cycling and walking segments
        intermediate_patterns, walk_to_origin_map, walk_from_destination_map = await asyncio.gather(
            self._route_bicycle_segments(context.waypoints[1:-1]),
            self.__route_walk_to_origin_stations(
                sorted_origin_nodes[:num_of_nodes],
                self._parse_coordinates(context.waypoints[0]),
                context
            ),
            self.__route_walk_from_destination_stations(
                sorted_destination_nodes[:num_of_nodes],
                self._parse_coordinates(context.waypoints[-1]),
                context
            ),
        )
        
        # Flatten intermediate cycling legs
        intermediate_legs = [
            leg 
            for pattern in intermediate_patterns
            for leg in pattern.legs
        ]
        
        # Build trip combinations for each origin destination station pair
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
        # Skip walking segment for public_bicycle mode
        if context.public_bicycle:
            return {}
        else:
            # Build walking tasks to origin stations
            tasks = {
                node.place.id: self._otp_foot_client.execute(
                    origin,
                    (node.place.latitude, node.place.longitude)
                )
                for node in nodes
            }

            results = await asyncio.gather(*tasks.values())

            # Map station id to walking patterns
            return dict(zip(tasks.keys(), results))
        
    async def __route_walk_from_destination_stations(
        self,
        nodes: List[BikeStationNode],
        destination: Tuple[float, float],
        context: PlanningContext
    ) -> Dict[str, List[TripPattern]]:
        # Skip walking segment for bicycle_public mode
        if context.bicycle_public:
            return {}
        else:
            # Build walking tasks from destination stations
            tasks = {
                node.place.id: self._otp_foot_client.execute(
                    (node.place.latitude, node.place.longitude),
                    destination
                )
                for node in nodes
            }

            results = await asyncio.gather(*tasks.values())

            # Map station id to walking patterns
            return dict(zip(tasks.keys(), results))

    async def __build_trip(
        self,
        trip_context: TripContext
    ) -> TripPattern | None:
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
                return None
            
            trip_pattern = deepcopy(walk_patterns[0])
        
        # Compute first cycling segment
        if len(trip_context.context.waypoints) > 2:
            result = await self._route_bicycle_segments([
                origin_bike_station,
                trip_context.context.waypoints[1]
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

        # Compute final cycling segment if needed
        if len(trip_context.context.waypoints) > 2:
            result = await self._route_bicycle_segments([
                trip_context.context.waypoints[-2],
                destination_bike_station
            ])

            if not result:
                return None

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

        # Append final walking segment if needed
        if not trip_context.context.bicycle_public:
            walk_patterns = trip_context.walk_from_destination_map[trip_context.destination_node.place.id]
            if not walk_patterns:
                return None
            trip_pattern.legs.extend(walk_patterns[0].legs)

        # Adjust trip timing
        PatternUtils.justify_time(
            trip_pattern,
            trip_context.context.time_cursor,
            self._ctx.data.arrive_by
        )

        # Set final aimed end time
        trip_pattern.aimedEndTime = trip_pattern.legs[-1].aimedEndTime
        return trip_pattern
    
    def __station_coordinates_str(self, node: BikeStationNode) -> str:
        # Convert station coordinates to string format
        return f"{node.place.latitude}, {node.place.longitude}"

    def __create_station_wait_leg(
        self,
        place: Place,
        origin: bool,
        selected_index: int,
        stations: List[BikeStationNode],
    ) -> Leg:
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

    def __prepare_wait_leg(self):
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
