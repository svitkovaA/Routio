"""
file: vehicle_positions.py

API endpoint for retrieving current vehicle positions based on a list of GTFS
trip_ids.
"""

from typing import List
from fastapi import APIRouter
from service.gtfs_rt_service import GTFSRTService

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
    gtfs_rt_service = GTFSRTService.get_instance()

    return gtfs_rt_service.get_vehicle_positions(data)

# End of file vehicle_positions.py
