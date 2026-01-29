"""
file: vehicle_positions.py

API endpoint for retrieving current vehicle positions
based on a list of GTFS trip_ids
"""

from typing import Dict, List
from fastapi import APIRouter
from services.gtfs_gbfs_service import get_vehicle_position

# Create a router instance
router = APIRouter()

@router.post("/vehiclePositions")
def vehicle_positions(data: List[int]):
    """
    Docstring for vehicle_positions
    
    Args:
        data: List of GTFS trip ids

    Returns:
        Dict[int, Dict[str, float]]: Mapping of trip_id to its current latitude and longitude.
    """
    print("endpoint: vehiclePositions")

    # Dictionary for mapping trip_id to lat, lon
    trip_id_to_position: Dict[int, Dict[str, float]] = {}

    # Iterate over all requested trip_ids
    for trip_id in data:

        # Retrieve vehicle position for a given trip_id
        pos = get_vehicle_position(trip_id)

        # Store the position if it exists
        if pos is not None:
            trip_id_to_position[trip_id] = {"lat": pos[0], "lon": pos[1]}

    return trip_id_to_position

# End of file vehicle_positions.py
