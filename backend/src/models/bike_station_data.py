from typing import Any, List
from pydantic import BaseModel
from models.route_data import RouteData


class BikeStationData(BaseModel):
    origin_bike_station: bool
    new_index: int
    bike_stations: List[Any]
    legs: List[Any]
    leg_index: int
    modes: List[str]
    original_legs: List[Any]
    route_data: RouteData
    bike_rack: bool
