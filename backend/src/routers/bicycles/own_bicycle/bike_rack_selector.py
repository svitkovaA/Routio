"""
file: bike_rack_selector.py

Bicycle rack selection and ranking logic.
"""

from typing import List, Tuple
from database.db import create_conn
from routers.bicycles.selector_base import SelectorBase
from models.route import BikeRackNode, BikeRackPlace, RackRow

class BikeRackSelector(SelectorBase):
    """
    Selects and ranks bicycle parking racks near destination.
    """
    async def select_racks(
        self,
        bicycle_public: bool,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
    ) -> List[BikeRackNode]:
        """
        Select optimal bicycle parking racks near destination.

        Args:
            bicycle_public: If true, direction filtering is applied
            origin: Origin coordinates in format lat,lon
            destination: Destination coordinates in format lat,lon

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

        # Retrieve scoring weights
        angle_weight, distance_weight = self.__get_weights(bicycle_public)

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
            in_forward = (
                not bicycle_public
                or self._is_in_forward_direction(
                    vector_destination_origin,
                    vector_destination_station
                )
            )

            # Compute normalized angular similarity
            normalized_angle = self._compute_normalized_angle(
                vector_destination_origin,
                vector_destination_station
            )

            # Compute final weighted score
            rack.score = (
                angle_weight * normalized_angle +
                distance_weight * (self._max_distance - rack.distance) / self._max_distance
            )
        
            # Separate forward and fallback racks
            if in_forward:
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

        query = """
            SELECT
                osm_id,
                lat,
                lon,
                capacity,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                ) AS distance
            FROM bicycle_racks
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
                $3
            )
            ORDER BY distance;
        """

        # Execute async database query
        async with create_conn() as conn:                                  # type: ignore
            rows = await conn.fetch(query, lon, lat, self._max_distance)   # type: ignore

        racks: List[BikeRackNode] = []

        # Convert raw DB rows
        for raw_row in rows:                                                # type: ignore
            try:
                row = RackRow.model_validate(dict(raw_row))                 # type: ignore
            except Exception:
                continue

            racks.append(
                BikeRackNode(
                    distance=row.distance,
                    place=BikeRackPlace(
                        latitude=row.lat,
                        longitude=row.lon,
                        name="Bike rack",
                        capacity=row.capacity if row.capacity is not None else 5
                    )
                )
            )

        return racks

    @staticmethod
    def __get_weights(bicycle_public: bool) -> Tuple[float, float]:
        """
        Returns scoring weights for bicycle rack selection. Weights
        correspond to: (angle_weight, distance_weight)

        Args:
            bicycle_public: Determines scoring emphasis.

        Returns:
            Tuple of two weight coefficients
        """
        # If bicycle_ public emphasize direction alignment
        if bicycle_public:
            return 0.6, 0.4
        # Otherwise emphasize distance
        return 0.4, 0.6

# End of file bike_rack_selector.py
