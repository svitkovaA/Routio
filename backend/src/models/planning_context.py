from datetime import datetime
from typing import List
from pydantic import BaseModel

class PlanningContext(BaseModel):
    waypoints: List[str]
    time_cursor: datetime
    public_bicycle: bool = False
    bicycle_public: bool = False
