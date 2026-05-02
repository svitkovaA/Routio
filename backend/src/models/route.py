"""
file: route.py

Defines core routing domain models used by the routing engine.
"""

from __future__ import annotations
from typing import Dict, List, Literal, Tuple
from datetime import datetime
from pydantic import BaseModel, model_validator
from zoneinfo import ZoneInfo

# Default timezone for route time normalization
TZ = ZoneInfo("Europe/Bratislava")

# Transport modes that do not depend on departure time
TIME_INDEPENDENT_MODES = ["bicycle", "foot"]

# Transport modes that depend on departure time
TIME_DEPENDENT_MODES = ["bus", "tram", "rail", "trolleybus", "metro", "water"]

# Transport mode for a single leg
Mode = Literal[
    "bus", "tram", "rail", "trolleybus", "metro", "water",
    "foot", "bicycle", "wait", "transfer"
]

# High level routing configuration modes for routing engine
RoutingMode = Literal[
    "bicycle", "foot", "walk_transit", "public_bicycle",
    "bicycle_public", "multimodal"
]

class Quay(BaseModel):
    """ Represents a public transport stop """
    id: str                                     # Unique quay identifier
    name: str                                   # Quay name, display name 

class PassingTime(BaseModel):
    """" Represents scheduled passing time at a stop """
    time: str                                   # Scheduled passing time

class ServiceJourney(BaseModel):
    """ Describes a public transport trip instance including stops and direction """
    quays: List[Quay]                           # Ordered list of stops
    direction: str = ""                         # Final stop, headsign
    passingTimes: List[Dict[str, PassingTime]]  # Timetable data per stop
    startOffset: int | None = None              # Index of the first stop
    currentIndex: int | None = None             # Index of the current vehicle stop

class PointOnLink(BaseModel):
    """ Encoded polyline representation of route geometry """
    points: str | List[str]                     # List of encoded polylines
    inactivePoints: List[str] = []              # List of encoded inactive polylines

class Line(BaseModel):
    """ Basic information about a transport line """
    publicCode: str                             # Public line number
    authority: Dict[str, str]                   # Agency name
    presentation: Dict[str, str | None]         # Route color and text color for visualisation

class PlaceBase(BaseModel):
    """ Base geographic location structure """
    latitude: float                             # Geographic latitude
    longitude: float                            # Geographic longitude

class RackRow(BaseModel):
    """ Represents a single bike rack row fetched from database query """
    lat: float                                  # Rack latitude
    lon: float                                  # Rack longitude
    distance: float                             # Distance from reference location
    capacity: int | None                        # Total rack capacity
    name: str | None                            # Rack name

class Place(PlaceBase):
    """ Extended place structure optionally containing name and quay reference"""
    name: str | None = None                     # Display name
    quay: Quay | None = None                    # Reference to a stop

class VehicleRealtimeData(BaseModel):
    """ Real-time vehicle position data """
    agencyName: str                             # GTFS agency name
    tripId: str                                 # GTFS trip identifier
    publicCode: str                             # Public line number
    mode: Mode                                  # Transport mode
    color: str                                  # Line display color
    lat: float = -1                             # Current latitude
    lon: float = -1                             # Current longitude
    direction: str                              # Direction, vehicle headsign
    startTime: datetime                         # Vehicle journey start time

    @model_validator(mode="after")
    def convert_datetime(self):
        self.startTime = self.startTime.replace(tzinfo=TZ)
        return self

class Departure(BaseModel):
    """ Represents a single departure option """
    departureTime: datetime                     # Scheduled departure time
    direction: str                              # Final stop, headsign
    tripId: str                                 # GTFS trip identifier

    @model_validator(mode="after")
    def convert_datetime(self):
        self.departureTime = self.departureTime.replace(tzinfo=TZ)
        return self

class OtherOptions(BaseModel):
    """ Alternative departure options for a public transport leg """
    departures: List[Departure] = []            # Ordered list of available departure alternatives
    currentIndex: int | None = None             # Selected departure index

class BikeStationInfo(PlaceBase):
    """ Information about bike station or rack for a route leg """
    rack: bool                                  # True if bike rack, false if bikesharing
    origin: bool                                # True if origin station, false if destination
    selectedBikeStationIndex: int               # Index of selected station
    bikeStations: List[BikeRackNode] | List[BikeStationNode]    # List of candidate racks/stations

class Leg(BaseModel):
    """ Represents a single route segment """
    mode: Mode                                  # Transport mode
    aimedStartTime: datetime = datetime.min     # Scheduled start time
    aimedEndTime: datetime = datetime.min       # Scheduled end time
    distance: float = 0                         # Distance
    duration: int                               # Duration
    pointsOnLink: PointOnLink                   # Route geometry
    fromPlace: Place | None = None              # Starting location
    toPlace: Place | None = None                # Ending location
    color: str | None = None                    # Display color
    otherOptions: OtherOptions | None = None    # Alternative departure
    walkMode: bool | None = None                # True if walking segment, false if transfer
    line: Line | None = None                    # Public transport line information
    serviceJourney: ServiceJourney | None = None    # Timetable details
    accumulatedDuration: int | None = None      # Accumulated duration up to this leg
    delays: Dict[str, int] = {}                 # Historical delay values per date
    bikeStationInfo: BikeStationInfo | None = None  # Bicycle station info
    tripId: str | None = None                   # Trip identifier
    vehicleRealtimeData: List[VehicleRealtimeData] = []   # Attached vehicle positions
    arrivalAfterDeparture: bool | None = None   # Inconsistency flag, arrival time is after next departure
    nonContinuousDepartures: bool | None = None # No more departures available
    zone_ids: List[int] | None = None           # Fare zone identifiers
    artificial: bool = False                    # Indicates artificial leg
    zeroBikesPredicted: bool = False            # Indicates zero bike prediction

    @model_validator(mode="after")
    def convert_datetime(self):
        self.aimedStartTime = self.aimedStartTime.replace(tzinfo=TZ)
        self.aimedEndTime = self.aimedEndTime.replace(tzinfo=TZ)
        return self

class TripPattern(BaseModel):
    """ Represents a complete trip consisting of multiple legs """
    legs: List[Leg]                             # Ordered list of legs
    aimedEndTime: datetime = datetime.min       # Scheduled end time
    aimedStartTime: datetime = datetime.min     # Scheduled start time
    modes: List[RoutingMode] = []               # Modes used in trip
    totalDuration: float | None = None          # Total duration
    totalDistance: float | None = None          # Total distance
    bikeDistance: float | None = None           # Total cycling distance
    walkDistance: float | None = None           # Total walking distance
    numOfTransfers: int | None = None           # Total number of transfers
    originalLegs: List[Leg] = []                # List of original legs
    tooLongWalkDistance: bool | None = None     # Constraint flag walking distance exceeding maximal allowed distance
    tooLongBikeDistance: bool | None = None     # Constraint flag cycling distance exceeding maximal allowed distance
    vehicleRealtimeData: List[VehicleRealtimeData] = []   # Real-time vehicle data
    totalTime: float = 0.0                      # Time from the start to end of the trip

    @model_validator(mode="after")
    def convert_datetime(self):
        self.aimedEndTime = self.aimedEndTime.replace(tzinfo=TZ)
        return self

class WaypointGroup(BaseModel):
    """ Grouping of consecutive waypoints that share the same transport mode """
    waypoints: List[str]                        # Ordered waypoint coordinates
    mode: RoutingMode                           # Assigned transport mode
    origin_station_id: str | None = None        # Optional origin bike station identifier
    destination_station_id: str | None = None   # Optional destination bike station identifier

    def get_key(
        self,
        timestamp: datetime
    ) -> Tuple[Tuple[str, ...], RoutingMode, datetime | None]:
        """ Generates a cache key for routing results """
        # Key for time independent modes
        if self.mode in TIME_INDEPENDENT_MODES:
            return (tuple(self.waypoints), self.mode, None)

        # Key for time dependent modes
        time_key = timestamp.replace(second=0, microsecond=0)
        return (tuple(self.waypoints), self.mode, time_key)
            

class OtherDeparture(BaseModel):
    """ Used for processing GTFS data when searching for other departure options """
    trip_id: str                                # GTFS trip identifier
    departure_time: datetime                    # Departure time
    direction: str                              # Tha final stop, trip headsign
    departure_time_str: str                     # Departure time string

    @model_validator(mode="after")
    def convert_datetime(self):
        self.departure_time = self.departure_time.replace(tzinfo=TZ)
        return self

class TripResponse(BaseModel):
    """ Response object returned by an OTP trip query """
    tripPatterns: List[TripPattern]             # List of computed trip patterns
    nextPageCursor: str | None = None           # Pagination cursor

class OTPPublicQueryResponse(BaseModel):
    """ Wrapper for OTP public transport GraphQL response """
    trip: TripResponse                          # Trip response data

class BikeRentalPlace(PlaceBase):
    """ Represents a bikesharing station returned by OTP """
    id: str = ""                                # Station identifier
    name: str = "Bike Station"                  # Station name
    bikesAvailable: int = 0                     # Available bicycles
    predictedBikes: int | None = None           # Predicted number of bikes

class BikeStationNodeBase(BaseModel):
    """ Base structure for a ranked bike station candidate """
    distance: float                             # Distance from reference location
    score: float = 0                            # Computed ranking score
    in_A_plane: bool = False

class BikeStationNode(BikeStationNodeBase):
    """ Represents a sharing bicycle station node """
    place: BikeRentalPlace                      # Station information

class BikeRackPlace(PlaceBase):
    """ Represents a bicycle rack location """
    name: str                                   # Rack name
    capacity: int                               # Total parking capacity

class BikeRackNode(BikeStationNodeBase):
    """ Represents a bike rack node """
    place: BikeRackPlace                        # Rack information

class BikeStationNodeWrapper(BaseModel):
    """ Wrapper object for a bike station node """
    node: BikeStationNode                       # Station node data

class Results(BaseModel):
    """ Represents routing response results """
    tripPatterns: List[TripPattern]             # List of computed trip patterns
    active: bool                                # Indicates whether the result is active

# End of file route.py
