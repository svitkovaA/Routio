from typing import List
from pydantic import BaseModel
from datetime import time, date

class LegPreferences(BaseModel):
    mode: str
    wait: int

class RouteData(BaseModel):
    waypoints: List[str]
    time: time
    date: date
    arrive_by: bool
    leg_preferences: List[LegPreferences]
    use_own_bike: bool
    mode: str
    max_transfers: int
    selected_modes: List[str]
    max_bike_distance:float
    bike_average_speed: float
    max_bikesharing_distance: float
    bikesharing_average_speed: float
    max_walk_distance: float
    walk_average_speed: float
    bikesharing_lock_time: int
    bike_lock_time: int
    route_preference: str
