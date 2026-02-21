from typing import TypedDict

class Suggestion(TypedDict):
    """ Search suggestion result """
    name: str                                   # Location name
    type: str                                   # Type of location
    country: str                                # Country where the location is situated
    city: str                                   # City name
    street: str | None                          # Street name if available
    lat: float                                  # Latitude of the suggested location
    lon: float                                  # Longitude of the suggested location
