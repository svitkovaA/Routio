from pydantic import BaseModel

class DepartureData(BaseModel):
    trip_pattern: dict
    public_leg_index: int
    selected_index: int

