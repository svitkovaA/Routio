from typing import Dict, List, Tuple
from pydantic import BaseModel

class LissyTrips(BaseModel):
    """ Represents a single trip entry in Lissy data """
    id: int | None                              # Trip identifier
    dep_time: str | None                        # Departure time

class LissyDelayTrips(BaseModel):
    """ Represents delay information for trips grouped by shape """
    shape_id: str                               # Identifier of the route shape
    stops: str                                  # Stop sequence
    stopOrder: List[str] = []                   # Ordered list of stop identifiers
    trips: List[LissyTrips]                     # List of trips associated with this shape

class LissyAvailableRoute(BaseModel):
    """ Represents an available route in Lissy data """
    route_short_name: str                       # Short name, number of the route
    id: int                                     # Route identifier

class LissyRouteData(BaseModel):
    """ Represents processed route data grouped by shape """
    shape_id: str                               # Identifier of the route shape
    stopOrder: List[str]                        # Ordered list of stop identifiers
    trips_by_time: Dict[str, int] = {}          # Maps departure time to trip id

class LissyShapeStop(BaseModel):
    """ Represents a stop belonging to a specific shape """
    stop_name: str                              # Name of the stop

class LissyShape(BaseModel):
    """ Represents geometric shape data of a route """
    coords: List[List[Tuple[float, float]]]     # Nested list of coordinates
    stops: List[LissyShapeStop]                 # List of stops along the shape

class LissyShapeTrips(BaseModel):
    """ Represents shape to stop mapping for trips """
    shape_id: int                               # Identifier of the route shape
    stops: str                                  # Stop sequence

class LissyShapes(BaseModel):
    """ Represents shape definitions grouped by route """
    route_short_name: str                       # Short name, number of the route
    route_color: str                            # Hexadecimal color code of the route
    trips: List[LissyShapeTrips]                # List of shape trip mappings

# End of file lissy.py
