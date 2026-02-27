from typing import List, Literal, Tuple
import numpy as np
from service.gbfs_service import GBFSService
from routers.bicycles.selector_base import SelectorBase
from models.route import BikeStationNode, BikeStationNodeWrapper
from models.planning_context import PlanningContext
from otp.bicycle_stations import OTPBicycleStations
from routing_engine.routing_context import RoutingContext

class BikeStationSelector(SelectorBase):
    def __init__(self, context: RoutingContext):
        super().__init__()
        self.__bicycle_stations_otp_client = OTPBicycleStations(context)
        self.__gbfs_service = GBFSService.get_instance()

    async def select_origin_stations(
        self,
        origin: Tuple[float, float], 
        destination: Tuple[float, float],
        context: PlanningContext
    ) -> List[BikeStationNode]:
        """
        Selects and ranks optimal origin bike stations based on a weighted scoring model.
        The function evaluates nearby bike stations relative to the provided coordinates. 
        Each station is scored using a combination of:
            - Angle between coordinates
            - Number of available bikes in station
            - Distance from the origin

        Args:
            origin: Latitude and longitude of the first waypoint
            destination: Latitude and longitude of the second waypoint

        Returns:
            Top 10 highest ranked bicycle stations sorted by score in descending order
        """
        # Retrieve nearby bike stations within the maximum distance
        nodes = await self.__bicycle_stations_otp_client.execute(
            *origin,
            self._max_distance
        )

        # Create vector from origin to destination
        base_vector = self._direction_vector(origin, destination)

        # Get weights
        angle_weight, availability_weight, distance_weight = self.__origin_weights(context)

        return self.__score_and_rank(
            nodes,
            origin,
            base_vector,
            context,
            angle_weight,
            availability_weight,
            distance_weight,
            "origin"
        )

    async def select_destination_stations(
        self,
        origin: tuple[float, float], 
        destination: tuple[float, float],
        context: PlanningContext
    ) -> List[BikeStationNode]:
        """
        Selects and ranks optimal destination bike stations based on a weighted scoring model.
        The function evaluates nearby bike stations relative to the provided coordinates. 
        Each station is scored based on:
            - Angle between coordinates
            - Available docking spaces
            - Distance from the destination

        Args:
            origin: Latitude and longitude of the first waypoint
            destination: Latitude and longitude of the second waypoint
        
        Returns:
            Top 10 highest ranked bicycle stations sorted by score in descending order
        """
        # Retrieve nearby bike stations within the maximum distance
        nodes = await self.__bicycle_stations_otp_client.execute(
            *destination,
            self._max_distance
        )

        # Create vector from destination to origin
        base_vector = self._direction_vector(destination, origin)

        # Get weights
        angle_weight, availability_weight, distance_weight = self.__destination_weights(context)

        return self.__score_and_rank(
            nodes,
            destination,
            base_vector,
            context,
            angle_weight,
            availability_weight,
            distance_weight,
            "destination"
        )

    def __score_and_rank(
        self,
        nodes: List[BikeStationNodeWrapper],
        reference_point: Tuple[float, float],
        base_vector: np.ndarray,
        context: PlanningContext,
        angle_weight: float,
        availability_weight: float,
        distance_weight: float,
        scoring_type: Literal["origin", "destination"]
    ) -> List[BikeStationNode]:
        scored_nodes: List[BikeStationNode] = []
        discarded_nodes: List[BikeStationNode] = []

        # Iterate over all nodes
        for wrapper in nodes:
            node = wrapper.node
            
            # Skip stations with no available bicycles or docks
            station_availability = self.__compute_availability(node, scoring_type)
            if station_availability is None:
                continue

            # Create vector from reference point to current station
            candidate_vector = self._direction_vector(
                reference_point,
                (node.place.latitude, node.place.longitude)
            )

            # Keep only stations that lie in the forward direction
            in_forward = (
                not (
                    context.public_bicycle 
                    if scoring_type == "origin" 
                    else context.bicycle_public
                ) or self._is_in_forward_direction(
                    base_vector,
                    candidate_vector
                )
            )

            # Compute cosine similarity between direction vectors
            normalized_angle = self._compute_normalized_angle(
                base_vector,
                candidate_vector
            )

            # Compute final weighted score
            node.score = (
                angle_weight * normalized_angle + 
                availability_weight * station_availability +
                distance_weight * (self._max_distance - node.distance) / self._max_distance
            )

            if in_forward:
                scored_nodes.append(node)
            else:
                discarded_nodes.append(node)

        return self._sort_and_limit(scored_nodes, discarded_nodes)
    
    def __compute_availability(
        self,
        node: BikeStationNode,
        scoring_type: Literal["origin", "destination"]
    ) -> float | None:
        # Origin bike stations
        if scoring_type == "origin":
            bikes = node.place.bikesAvailable or 0
            if bikes == 0:
                return None
            return np.clip(bikes, 0, 5) / 5
        
        # Destination bike stations
        station_id = node.place.id
        if not station_id:
            return None

        capacity = self.__gbfs_service.get_capacity(station_id)
        if capacity is None:
            return 1.0

        bikes = node.place.bikesAvailable or 0
        free_ratio = (capacity - bikes) / capacity

        if free_ratio <= 0:
            return None

        return float(np.clip(free_ratio, 0.0, 1.0))

    @staticmethod
    def __origin_weights(context: PlanningContext) -> Tuple[float, float, float]:
        if context.public_bicycle:
            return 0.4, 0.3, 0.3
        return 0.1, 0.4, 0.5
    
    @staticmethod
    def __destination_weights(context: PlanningContext) -> Tuple[float, float, float]:
        if context.bicycle_public:
            return 0.4, 0.3, 0.3
        return 0.3, 0.3, 0.4
