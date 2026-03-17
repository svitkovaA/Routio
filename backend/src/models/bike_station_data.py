"""
file: bike_station_data.py

Defines request model used when recalculating a route after a user changes the
selected bicycle station or rack.
"""

from typing import List
from pydantic import BaseModel
from models.route import BikeRackNode, BikeStationNode, Leg, RoutingMode
from models.route_data import RouteData

class BikeStationData(BaseModel):
    """ Request model used when recalculating a route after changing a bike station selection """
    origin_bike_station: bool       # True if the modified station is the origin station, false otherwise
    new_index: int                  # Index of the newly selected bike station
    bike_stations: List[BikeRackNode] | List[BikeStationNode]   # List of available bike stations
    legs: List[Leg]                 # Current list of trip legs that need to be updated
    leg_index: int                  # Index of the leg associated with the bike station that should be recalculated
    modes: List[RoutingMode]        # Transport modes used for each route segment
    original_legs: List[Leg]        # Original legs before modification
    route_data: RouteData           # Route preferences

# End of file bike_station_data.py
