"""
file: planning_context.py

Defines planning context used internally by the routing engine during route 
computation and waypoint grouping.
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel

class PlanningContext(BaseModel):
    waypoints: List[str]                        # Ordered list of waypoint coordinates
    time_cursor: datetime                       # Current time reference
    public_bicycle: bool = False                # True if routing includes public_transport_bicycle routing strategy
    bicycle_public: bool = False                # True if routing includes bicycle_public_transport routing strategy
    use_bisector: bool = False                  # True if bisector is to be used
    origin_station_id: str | None = None        # Optional origin bike station identifier
    destination_station_id: str | None = None   # Optional destination bike station identifier

# End of file planning_context.py
