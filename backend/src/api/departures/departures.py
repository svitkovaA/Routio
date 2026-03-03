"""
file: departures.py

Defines API endpoint for handling alternative public transport departure
selection and triggering trip recalculation.
"""

from fastapi import APIRouter
from api.departures.departure_updater import DepartureUpdater
from models.departure_data import DepartureData

# Router instance for other departure endpoint
router = APIRouter()

@router.post("/otherDepartures")
async def other_departures(data: DepartureData):
    """
    Recalculates a trip pattern after a user selects a different public
    transport departure option.

    Args:
        data: Request payload

    Returns:
        Updated trip pattern with recalculated leg timings
    """
    return DepartureUpdater.update_departures(data)

# End of file departures.py
