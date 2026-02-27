"""
file: departures.py

API endpoint for handling alternative public transport departures.
"""

from fastapi import APIRouter
from api.departures.departure_updater import DepartureUpdater
from models.departure_data import DepartureData

router = APIRouter()

@router.post("/otherDepartures")
async def other_departures(data: DepartureData):
    return DepartureUpdater.update_departures(data)

# End of file departures.py
