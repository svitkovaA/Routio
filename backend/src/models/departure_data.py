from pydantic import BaseModel
from typing import Dict, Any

class DepartureData(BaseModel):
    trip_pattern: Dict[str, Any]
    public_leg_index: int
    selected_index: int

