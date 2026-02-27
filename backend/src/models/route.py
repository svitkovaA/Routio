from __future__ import annotations
from typing import Dict, List, Any, Literal, Tuple
from datetime import datetime
from pydantic import BaseModel

# Transport modes for a single leg
TIME_INDEPENDENT_MODES = ["bicycle", "foot"]

# Transport modes for a single leg
TIME_DEPENDENT_MODES = ["bus", "tram", "rail", "trolleybus", "metro", "water"]

# Represents the transport mode of a single leg
Mode = Literal["bus", "tram", "rail", "trolleybus", "metro", "water", "foot", "bicycle", "wait", "transfer"]

# Represents high level routing configuration for routing engine
RoutingMode = Literal["bicycle", "foot", "walk_transit", "public_bicycle", "bicycle_public", "multimodal"]

class Quay(BaseModel):
    """ Represents a public transport stop """
    id: str                                     # Quay identifier
    name: str                                   # Quay name 

class PassingTime(BaseModel):
    """" Represents scheduled passing time at a stop """
    time: str                                   # Time when passing stop

class ServiceJourney(BaseModel):
    """ Describes a public transport trip instance including stops and direction """
    quays: List[Quay]                           # Ordered list of stops
    direction: str = ""                         # Final stop, headsign
    passingTimes: List[Dict[str, PassingTime]]  # Timetable data

class PointOnLink(BaseModel):
    """ Encoded polyline representation of route geometry """
    points: str | List[str]                     # Encoded polyline or list of encoded polylines

class Line(BaseModel):
    """ Basic information about a transport line """
    publicCode: str                             # Public line number

class PlaceBase(BaseModel):
    """ Base geographic location """
    latitude: float                             # Geographic latitude
    longitude: float                            # Geographic longitude

class RackRow(BaseModel):
    """ Represents a single bike rack row fetched from the database query """
    lat: float                                  # Latitude coordinate of the bike rack
    lon: float                                  # Longitude coordinate of the bike rack
    distance: float                             # Distance from the reference location
    capacity: int | None                        # Total rack capacity

class Place(PlaceBase):
    """ Extended place structure optionally containing name and quay reference"""
    name: str | None = None                     # Display name of the location
    quay: Quay | None = None                    # Reference to a stop

class VehiclePositions(BaseModel):
    """ Real-time vehicle position data """
    tripId: int                                 # Unique identifier of the GTFS trip
    publicCode: str                             # Public line number
    mode: Mode                                  # Transport mode
    color: str                                  # Line color used for visualization
    lat: float = -1                             # Current vehicle latitude
    lon: float = -1                             # Current vehicle longitude
    direction: str                              # Direction, headsign of the vehicle

class Departure(BaseModel):
    """ Represents a single departure option for a public transport leg """
    departureTime: datetime                     # Scheduled departure time
    direction: str                              # The final stop of the trip
    tripId: int                                 # Unique identifier of the GTFS trip

class OtherOptions(BaseModel):
    """ Alternative departure options for a public transport leg """
    departures: List[Departure] = []            # Ordered list of available departure alternatives
    currentIndex: int | None = None             # Index of the currently selected departure within the list

class BikeStationInfo(PlaceBase):
    """ Contains information about bike station or rack options for a route leg """
    rack: bool                                  # Indicates whether it is a bike rack, true, or bikesharing station, false
    origin: bool                                # True if the bike station selection applies to the trip origin, False if to destination
    selectedBikeStationIndex: int               # Index of the currently selected bike station/rack in the bikeStations list
    bikeStations: List[BikeRackNode] | List[BikeStationNode]    # List of candidate bike racks or bikesharing stations

class Leg(BaseModel):
    """ Leg containing public transport, bicycle or visualization data """
    mode: Mode                                  # Transport mode
    aimedStartTime: datetime = datetime.min     # Scheduled start time
    aimedEndTime: datetime = datetime.min       # Scheduled end time
    distance: float = 0                         # Distance in meters
    duration: int                               # Duration in seconds
    pointsOnLink: PointOnLink                   # Route geography
    fromPlace: Place | None = None              # Starting location of the leg
    toPlace: Place | None = None                # Ending location of the leg
    color: str | None = None                    # Display color
    otherOptions: OtherOptions | None = None    # Alternative departure options for public transport legs
    walkMode: bool | None = None                # Indicates that this leg is walking segment not just transfer
    line: Line | None = None                    # Public transport line information
    serviceJourney: ServiceJourney | None = None    # Detailed timetable information including stops and direction
    accumulatedDuration: int | None = None      # Duration accumulated up to this leg
    delays: Dict[str, int] = {}                 # Historical delay values per date
    bikeStationInfo: BikeStationInfo | None = None  # Information about bicycle stations
    tripId: int | None = None                   # Identifier of the public transport trip
    vehiclePositions: List[VehiclePositions] = []   # Actual vehicle position data attached to this leg
    arrivalAfterDeparture: bool | None = None   # Indicates inconsistency where arrival time is after next departure
    nonContinuousDepartures: bool | None = None # True if no further alternative departures are available

class TripPattern(BaseModel):
    """ Represents a complete trip consisting of multiple legs """
    legs: List[Leg]                             # List of legs in trip pattern
    aimedEndTime: datetime = datetime.min       # Scheduled end time of the trip pattern
    modes: List[RoutingMode] = []               # Modes used per segment
    polyInfo: List[Any] = []                    # Polyline info
    totalDuration: float | None = None          # Total duration
    totalDistance: float | None = None          # Total distance
    bikeDistance: float | None = None           # Total cycling distance
    walkDistance: float | None = None           # Total walking distance
    numOfTransfers: int | None = None           # Total number of transfers
    originalLegs: List[Leg] = []                # List of original legs
    tooLongWalkDistance: bool | None = None     # Constraint flag walking distance exceeding maximal allowed distance
    tooLongBikeDistance: bool | None = None     # Constraint flag cycling distance exceeding maximal allowed distance
    bikeSegmentFound: bool | None = None        # Indicates present of cycling
    vehiclePositions: List[VehiclePositions] = []   # List of information about vehicle positions

class WaypointGroup(BaseModel):
    """ Grouping of consecutive waypoints that share the same transport mode """
    group: List[str]                            # Ordered list of waypoint coordinates  TODO rename to waypoints
    mode: RoutingMode                           # Assigned transport mode for this waypoint group
    tripPatterns: List[TripPattern] = []        # Precomputed routing results for this group    TODO possibly not used

    def get_key(
        self,
        timestamp: datetime
    ) -> Tuple[Tuple[str, ...], RoutingMode, datetime | None]:
        # Key for time independent modes
        if self.mode in TIME_INDEPENDENT_MODES:
            return (tuple(self.group), self.mode, None)

        # Key for time dependent modes
        time_key = timestamp.replace(second=0, microsecond=0)
        return (tuple(self.group), self.mode, time_key)
            

class OtherDeparture(BaseModel):
    """ Used for processing GTFS data when searching for other departure options """
    trip_id: int                                # Unique GTFS trip identifier
    departure_time: datetime                    # Departure time
    direction: str                              # Tha final stop, trip headsign
    departure_time_str: str                     # Parsed datetime object

class TripResponse(BaseModel):
    """ Represents a response object returned by an OTP trip query """
    tripPatterns: List[TripPattern]             # List of computed trip patterns
    nextPageCursor: str | None = None           # Cursor used for pagination when requesting additional results

class OTPPublicQueryResponse(BaseModel):
    """ Wrapper structure for OTP public transport GraphQL response """
    trip: TripResponse                          # Main trip response object returned by OTP

class BikeRentalPlace(PlaceBase):
    """ Represents a bikesharing station returned by OTP """
    id: str = ""                                # Unique station identifier
    name: str = "Bike Station"                  # Station name
    bikesAvailable: int = 0                     # Number of bicycles currently available
    spacesAvailable: int = 0                    # Number of free docking spaces
    allowDropoff: bool = False                  # Indicates whether bike drop-off is allowed at this station

class BikeStationNodeBase(BaseModel):
    """ Base structure for a ranked bike station candidate """
    distance: float                             # Distance from the reference location
    score: float = 0                            # Computed ranking score used for station selection

class BikeStationNode(BikeStationNodeBase):
    """ Represents a bike rental station node """
    place: BikeRentalPlace                      # Bikesharing place information

class BikeRackPlace(PlaceBase):
    """ Represents a bicycle rack location """
    name: str                                   # Rack name
    capacity: int                               # Total number of bike parking spaces

class BikeRackNode(BikeStationNodeBase):
    """ Represents a bike rack node """
    place: BikeRackPlace                        # Bike rack information

class BikeStationNodeWrapper(BaseModel):
    """ Wrapper object for a bike station node """
    node: BikeStationNode                       # Bike station node data

class Results(BaseModel):
    """ Represents routing response results """
    tripPatterns: List[TripPattern]             # List of computed trip patterns
    active: bool                                # Indicates whether the routing result is active

# End of file route.py
