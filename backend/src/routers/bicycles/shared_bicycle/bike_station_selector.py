"""
file: bike_station_selector.py

Bike station selection and ranking logic.
"""

from datetime import datetime
from typing import List, Literal, Tuple
import numpy as np
from service.prediction_service import PredictionService
from service.gbfs_service import GBFSService
from routers.bicycles.selector_base import SelectorBase
from models.route import TZ, BikeStationNode, BikeStationNodeWrapper
from models.planning_context import PlanningContext
from otp.bicycle_stations import OTPBicycleStations
from routing_engine.routing_context import RoutingContext

class BikeStationSelector(SelectorBase):
    """
    Selects and ranks bike stations for shared bicycle routing.
    """
    def __init__(self, context: RoutingContext):
        super().__init__()
        self.__bicycle_stations_otp_client = OTPBicycleStations(context)
        self.__gbfs_service = GBFSService.get_instance()
        self.__prediction_service = PredictionService.get_instance()

    async def select_origin_stations(
        self,
        origin: Tuple[float, float], 
        destination: Tuple[float, float],
        context: PlanningContext,
        bisector_vector: np.ndarray | None = None
    ) -> List[BikeStationNode]:
        """
        Selects and ranks candidate origin bicycle stations.

        Args:
            origin: Latitude and longitude of the first waypoint
            destination: Latitude and longitude of the second waypoint
            context: Planning context affecting scoring weights
            bisector_vector: Bisector of the angle or None

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

        # Compute forward vector
        forward_vector = self._compute_forward_vector(
            origin,
            destination,
            bisector_vector,
            origin_flag=True
        )

        # Get scoring weights for origin selection
        angle_weight, availability_weight, distance_weight = self.__origin_weights(context)

        # Rank the candidates
        return self.__score_and_rank(
            nodes,
            origin,
            destination,
            base_vector,
            forward_vector,
            context,
            angle_weight,
            availability_weight,
            distance_weight,
            "origin",
            bisector_vector
        )

    async def select_destination_stations(
        self,
        origin: tuple[float, float], 
        destination: tuple[float, float],
        context: PlanningContext,
        bisector_vector: np.ndarray | None = None
    ) -> List[BikeStationNode]:
        """
        Selects and ranks candidate destination bicycle stations .

        Args:
            origin: Latitude and longitude of the first waypoint
            destination: Latitude and longitude of the second waypoint
            context: Planning context affecting scoring weights
            bisector_vector: Bisector of the angle or None
        
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

        # Compute forward vector
        forward_vector = self._compute_forward_vector(
            origin,
            destination,
            bisector_vector
        )

        # Get scoring weights for destination selection
        angle_weight, availability_weight, distance_weight = self.__destination_weights(context)

        # Rank the candidates
        return self.__score_and_rank(
            nodes,
            destination,
            origin,
            base_vector,
            forward_vector,
            context,
            angle_weight,
            availability_weight,
            distance_weight,
            "destination",
            bisector_vector
        )

    def __score_and_rank(
        self,
        nodes: List[BikeStationNodeWrapper],
        reference_point: Tuple[float, float],
        b_point: Tuple[float, float],
        base_vector: np.ndarray,
        forward_vector: np.ndarray,
        context: PlanningContext,
        angle_weight: float,
        availability_weight: float,
        distance_weight: float,
        scoring_type: Literal["origin", "destination"],
        bisector_vector: np.ndarray | None
    ) -> List[BikeStationNode]:
        """
        Computes weighted score for each station and returns ranked list.

        Args:
            nodes: List of nearby bike station
            reference_point: Geographic reference in format lat, lon
            base_vector: Direction vector representing intended travel direction
            context: Planning context containing routing flags
            angle_weight: Weight coefficient for angular alignment component
            availability_weight: Weight coefficient for availability component
            distance_weight: Weight coefficient for distance component
            scoring_type: Determines scoring behavior
            bisector_vector: Bisector of the angle or None

        Returns:
            List of best bike stations objects sorted by descending score
        """
        scored_nodes: List[BikeStationNode] = []
        discarded_nodes: List[BikeStationNode] = []

        # Evaluate each candidate station
        for wrapper in nodes:
            node = wrapper.node
            
            # Compute normalized availability score
            station_availability = self.__compute_availability(node, scoring_type, context.time_cursor)

            # Skip stations with no available bicycles or docks
            if station_availability is None:
                continue

            # Create vector from reference point to station
            candidate_vector = self._direction_vector(
                reference_point,
                (node.place.latitude, node.place.longitude)
            )

            # Determine whether station lies in forward direction
            in_forward = (
                not (
                    context.public_bicycle 
                    if scoring_type == "origin" 
                    else context.bicycle_public
                ) or self._is_in_forward_direction(
                    forward_vector,
                    candidate_vector
                )
            )

            # Compute normalized angular similarity
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

            # Separate forward and non forward stations
            if in_forward:
                if bisector_vector is not None:
                    # Compute vector to station
                    vector_b_station = self._direction_vector(
                        b_point,
                        (node.place.latitude, node.place.longitude)
                    )

                    # Compute vector cross product
                    side = self._cross2d(
                        bisector_vector,
                        vector_b_station
                    )

                    # Determine in which plane is the station
                    node.in_A_plane = bool(
                        np.sign(side) > 0
                        if scoring_type == "destination"
                        else np.sign(side) <= 0
                    )

                scored_nodes.append(node)
            else:
                discarded_nodes.append(node)

        # Sort and limit result set
        return self._sort_and_limit(scored_nodes, discarded_nodes)
    
    def __compute_availability(
        self,
        node: BikeStationNode,
        scoring_type: Literal["origin", "destination"],
        time_cursor: datetime
    ) -> float | None:
        """
        Computes normalized availability score for a bike station. The meaning
        of availability depends on scoring type.

        Args:
            node: Bike station node containing data
            scoring_type: Defines scoring mode, origin, evaluate available
                bicycles, destination, evaluate free docking capacity,
            tie_cursor: estimated arrival time to origin

        Returns:
            Normalized value in range (0,1)
        """
        # Destination station scoring
        station_id = node.place.id

        # Skip station if identifier is missing
        if not station_id:
            return None
        
        # Origin station scoring
        if scoring_type == "origin":

            # When planning in the past do not take bikes number into account
            if time_cursor < datetime.now(tz=TZ):
                return 1

            # Retrieve actual bike capacity
            bikes = node.place.bikesAvailable or 0

            # Get predicted number of bicycles
            node.place.predictedBikes = self.__prediction_service.predict_bikes(
                int(station_id),
                time_cursor
            )

            if node.place.predictedBikes is not None:
                if node.place.predictedBikes == 0:
                    return None

                # Normalize bicycle count
                return np.clip(node.place.predictedBikes, 0, 5) / 5

            # Skip station if no bicycles are available
            if bikes == 0:
                return None
            
            # Normalize bicycle count
            return np.clip(bikes, 0, 5) / 5

        # Retrieve station capacity from GBFS cache
        capacity = self.__gbfs_service.get_capacity(station_id)

        # If capacity is unknown, assume fully usable
        if capacity is None:
            return 1.0

        bikes = node.place.bikesAvailable or 0
        free_ratio = (capacity - bikes) / capacity

        # Skip station if no free docking slots available
        if free_ratio <= 0:
            return None

        return float(np.clip(free_ratio, 0.0, 1.0))

    @staticmethod
    def __origin_weights(context: PlanningContext) -> Tuple[float, float, float]:
        """
        Returns scoring weights for origin station selection. Weights
        correspond to: (angle_weight, availability_weight, distance_weight)

        Args:
            context: Planning context influencing scoring behavior

        Returns:
            Tuple of three weight coefficients
        """
        # In public bicycle mode, emphasize direction alignment
        if context.public_bicycle:
            return 0.4, 0.3, 0.3

        # Otherwise emphasize distance and availability
        return 0.1, 0.4, 0.5
    
    @staticmethod
    def __destination_weights(context: PlanningContext) -> Tuple[float, float, float]:
        """
        Returns scoring weights for destination station selection. Weights
        correspond to: (angle_weight, availability_weight, distance_weight)

        Args:
            context: Planning context influencing scoring behavior

        Returns:
            Tuple of three weight coefficients
        """
        # In bicycle_public mode, emphasize direction alignment
        if context.bicycle_public:
            return 0.4, 0.3, 0.3

        # Otherwise emphasize distance and availability
        return 0.3, 0.3, 0.4

# End of file bike_station_selector.py
