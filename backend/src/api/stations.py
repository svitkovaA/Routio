"""
file: stations.py

Defines API endpoint for retrieving bicycle station information.
"""

from fastapi import APIRouter
from service.gbfs_service import GBFSService

# Router instance for bicycle stations endpoint
router = APIRouter()

@router.get("/bicycleStations")
def get_bicycle_stations():
    """
    Retrieves bicycle station information.
    """
    gbfs_service = GBFSService.get_instance()
    return gbfs_service.get_station_info()

# End of file stations.py
