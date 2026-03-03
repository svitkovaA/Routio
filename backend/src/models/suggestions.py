"""
file: suggestions.py

Defines the Suggestion data model representing a single search result returned
by the location search endpoint.
"""

from pydantic import BaseModel

class Suggestion(BaseModel):
    """ Data model representing a single location search suggestion """
    name: str                                   # Location name
    type: str                                   # Type of location
    country: str                                # Country where the location is situated
    city: str                                   # City name
    street: str | None                          # Street name if available
    lat: float                                  # Latitude of the suggested location
    lon: float                                  # Longitude of the suggested location

# End of file suggestions.py
