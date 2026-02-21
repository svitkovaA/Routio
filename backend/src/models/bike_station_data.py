from typing import Any, List
from pydantic import BaseModel
from models.route_data import RouteData

class BikeStationData(BaseModel):
    """ Request model used when recalculating a route after changing a bike station selection """
    origin_bike_station: bool       # True if the modified station is the origin station, false otherwise
    new_index: int                  # Index of the newly selected bike station
    bike_stations: List[Any]        # List of available bike stations
    legs: List[Any]                 # Current list of trip legs that need to be updated
    leg_index: int                  # Index of the leg associated with the bike station that should be recalculated
    modes: List[str]                # Transport modes used for each route segment
    original_legs: List[Any]        # Original legs before modification
    route_data: RouteData           # Route preferences
    bike_rack: bool                 # True if the station represents a bike rack, false if shared bike station

# End of file bike_station_data.py
