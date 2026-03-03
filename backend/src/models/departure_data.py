"""
file: departure_data.py

Defines request model used when a user selects a different departure option
for a public transport leg.
"""

from pydantic import BaseModel
from models.route import TripPattern

class DepartureData(BaseModel):
    """ Request model used when the different departure option for a public transport leg is selected """
    trip_pattern: TripPattern       # The trip pattern that contains the public transport leg
    public_leg_index: int           # Index of the public transport leg inside the trip pattern
    selected_index: int             # Index of the newly selected departure option

# End of file departure_data.py
