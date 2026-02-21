from typing import List
from pydantic import BaseModel
from datetime import time, date

class LegPreferences(BaseModel):
    """ User preference for a specific route segment """
    mode: str                                   # Preferred transport mode for the segment
    wait: int                                   # Wait time in minutes before departure

class RouteData(BaseModel):
    """ Main routing configuration model including user preferences """
    waypoints: List[str]                        # Ordered list of waypoint coordinates
    time: time                                  # Selected departure or arrival time
    date: date                                  # Selected routing date
    arrive_by: bool                             # If true, compute route to arrive by selected time, if false to depart by selected time
    leg_preferences: List[LegPreferences]       # Preferences applied to individual route segments
    use_own_bike: bool                          # If true, user wants to use own bike, if false the share bicycles are being considered
    mode: str                                   # Global routing mode, if all route segments use the same mode, this specifies the mode, otherwise the multimodal mode is set
    max_transfers: int                          # Maximum allowed number of public transport transfers
    selected_modes: List[str]                   # List of allowed public transport modes
    max_bike_distance:float                     # Maximal allowed distance with own bicycle
    bike_average_speed: float                   # Average speed using own bicycle
    max_bikesharing_distance: float             # Maximal allowed distance with shared bicycle
    bikesharing_average_speed: float            # Average speed using shared bicycle
    max_walk_distance: float                    # Maximal walking allowed distance
    walk_average_speed: float                   # Average walk speed
    bikesharing_lock_time: int                  # Time required to unlock/lock a shared bicycle
    bike_lock_time: int                         # Time required to lock an own bicycle
    route_preference: str                       # Route optimization preference, e.g. fastest, shortest, maximum transfers

# End of file route_data.py
