"""
file: vehicle_realtime_data.py

API endpoint for retrieving real-time vehicle positions and delays based on
a list of GTFS trip_ids.
"""

from typing import List
from fastapi import APIRouter
from service.gtfs_rt_service import GTFSRTService

# Create a router instance
router = APIRouter()

@router.post("/vehicleRealtimeData")
def vehicle_realtime_data(data: List[int]):
    """
    Retrieves current vehicle positions and delays for given GTFS trip IDs.
    
    Args:
        data: List of GTFS trip ids

    Returns:
        Mapping trip_id to latitude and longitude coordinates and delay
    """
    gtfs_rt_service = GTFSRTService.get_instance()

    return gtfs_rt_service.get_vehicle_realtime_data(data)

# End of file vehicle_realtime_data.py
