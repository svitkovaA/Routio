from pydantic import BaseModel
from typing import Dict, Any

class DepartureData(BaseModel):
    """ Request model used when the different departure option for a public transport leg is selected """
    trip_pattern: Dict[str, Any]    # The trip pattern that contains the public transport leg
    public_leg_index: int           # Index of the public transport leg inside the trip pattern
    selected_index: int             # Index of the newly selected departure option

# End of file departure_data.py
