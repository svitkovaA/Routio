from pydantic import BaseModel
from models.types import TripPattern

class DepartureData(BaseModel):
    trip_pattern: TripPattern
    public_leg_index: int
    selected_index: int

