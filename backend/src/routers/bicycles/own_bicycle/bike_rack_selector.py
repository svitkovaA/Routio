"""
file: bike_rack_selector.py

Bicycle rack selection and ranking logic.
"""

from typing import List, Tuple
import numpy as np
from service.database_service import DatabaseService
from routers.bicycles.selector_base import SelectorBase
from models.route import BikeRackNode, BikeRackPlace, RackRow

class BikeRackSelector(SelectorBase):
    """
    Selects and ranks bicycle parking racks near destination.
    """
    def __init__(self):
        super().__init__()
        self.__database_service = DatabaseService.get_instance()

    async def select_racks(
        self,
        bicycle_public: bool,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        bisector_vector: np.ndarray | None
    ) -> List[BikeRackNode]:
        """
        Select optimal bicycle parking racks near destination.

        Args:
            bicycle_public: If true, direction filtering is applied
            origin: Origin coordinates in format lat,lon
            destination: Destination coordinates in format lat,lon
            bisector_vector: Bisector of the angle or None

        Returns:
            Ranked list of bicycle racks sorted by descending score
        """
        # Retrieve racks within configured max distance
        racks = await self.__find_bike_racks(*destination)

        # Vector representing travel direction
        vector_destination_origin = self._direction_vector(
            destination,
            origin
        )

        # Compute forward facing vector
        forward_vector = self._compute_forward_vector(
            origin,
            destination,
            bisector_vector
        )

        # Retrieve scoring weights
        angle_weight, capacity_weight, distance_weight = self._destination_weights()

        scored_racks: List[BikeRackNode] = []
        discarded_racks: List[BikeRackNode] = []

        # Evaluate each rack candidate
        for rack in racks:  
            # Direction vector from destination to rack
            vector_destination_station = self._direction_vector(
                destination,
                (rack.place.latitude, rack.place.longitude)
            )
            
            # Determine whether station lies in forward direction
            if not bicycle_public:
                in_forward = True
            else:
                in_forward = self._is_in_forward_direction(
                    forward_vector,
                    vector_destination_station
                )

            # Compute normalized angular similarity
            normalized_angle = self._compute_normalized_angle(
                vector_destination_origin,
                vector_destination_station
            )

            # Compute final weighted score
            rack.score = (
                angle_weight * normalized_angle +
                capacity_weight * (np.clip(rack.place.capacity, 0, 5) / 5) + 
                distance_weight * (self._max_distance - rack.distance) / self._max_distance
            )
        
            # Separate forward and fallback racks
            if in_forward:
                if bisector_vector is not None:
                    # Compute vector to station
                    vector_origin_station = self._direction_vector(
                        origin,
                        (rack.place.latitude, rack.place.longitude)
                    )

                    # Compute vector cross product
                    side = self._cross2d(
                        bisector_vector,
                        vector_origin_station
                    )

                    # Determine in which plane is the station
                    rack.in_A_plane = bool(np.sign(side) > 0)

                scored_racks.append(rack)
            else:
                discarded_racks.append(rack)

        # Sort and limited rack list
        return self._sort_and_limit(scored_racks, discarded_racks)
   
    async def __find_bike_racks(
        self,
        lat: float,
        lon: float,
    ) -> List[BikeRackNode]:
        """
        Finds bicycle racks within maximum distance from given location.

        Args:
            lat: Latitude of the search center
            lon: Longitude of the search center

        Returns:
            List of nearby bicycle racks
        """
        # Execute async database query
        rows = await self.__database_service.find_bike_racks(lat, lon, self._max_distance)

        racks: List[BikeRackNode] = []

        # Convert raw DB rows
        for raw_row in rows:
            try:
                row = RackRow.model_validate(dict(raw_row))
            except Exception:
                continue

            racks.append(
                BikeRackNode(
                    distance=row.distance,
                    place=BikeRackPlace(
                        latitude=row.lat,
                        longitude=row.lon,
                        name=row.name if row.name is not None else "Bike rack",
                        capacity=row.capacity if row.capacity is not None else 5
                    )
                )
            )

        return racks

# End of file bike_rack_selector.py
