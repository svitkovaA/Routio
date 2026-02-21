from typing import Dict, TypedDict, List, Any
from datetime import datetime

class Quay(TypedDict):
    """ Represents a public transport stop """
    id: str                                     # Quay identifier
    name: str                                   # Quay name 

class PassingTime(TypedDict):
    """" Represents scheduled passing time at a stop """
    time: str                                   # Time when passing stop

class ServiceJourney(TypedDict):
    """ Describes a public transport trip instance including stops and direction """
    quays: List[Quay]                           # Ordered list of stops
    direction: str                              # Final stop, headsign
    passingTimes: List[Dict[str, PassingTime]]  # Timetable data

class PointOnLink(TypedDict):
    """ Encoded polyline representation of route geometry """
    points: str | List[str]                     # Encoded polyline or list of encoded polylines

class Line(TypedDict):
    """ Basic information about a transport line """
    publicCode: str                             # Public line number

class PlaceBase(TypedDict):
    """ Base geographic location """
    latitude: float                             # Geographic latitude
    longitude: float                            # Geographic longitude

class Place(PlaceBase, total=False):
    """ Extended place structure optionally containing name and quay reference"""
    name: str                                   # Display name of the location
    quay: Quay                                  # Reference to a stop

class VehiclePositions(TypedDict):
    """ Real-time vehicle position data """
    tripId: int                                 # Unique identifier of the GTFS trip
    publicCode: str                             # Public line number
    mode: str                                   # Transport mode
    color: str                                  # Line color used for visualization
    lat: float                                  # Current vehicle latitude
    lon: float                                  # Current vehicle longitude
    direction: str                              # Direction, headsign of the vehicle

class Departure(TypedDict):
    """ Represents a single departure option for a public transport leg """
    departureTime: str                          # Scheduled departure time
    direction: str                              # The final stop of the trip
    tripId: int                                 # Unique identifier of the GTFS trip

class OtherOptions(TypedDict):
    """ Alternative departure options for a public transport leg """
    departures: List[Departure]                 # Ordered list of available departure alternatives
    currentIndex: int | None                    # Index of the currently selected departure within the list

class LegBase(TypedDict):
    """ Base structure for a single segment of a trip """
    mode: str                                   # Transport mode
    aimedStartTime: str                         # Scheduled start time
    aimedEndTime: str                           # Scheduled end time
    distance: float                             # Distance in meters
    duration: int                               # Duration in seconds
    pointsOnLink: PointOnLink                   # Route geography

class Leg(LegBase, total=False):
    """ Extended leg containing optional public transport,
    bicycle or visualization data """
    fromPlace: Place                            # Starting location of the leg
    toPlace: Place                              # Ending location of the leg
    color: str                                  # Display color
    otherOptions: OtherOptions                  # Alternative departure options for public transport legs
    walkMode: bool                              # Indicates that this leg is walking segment not just transfer
    line: Line                                  # Public transport line information
    serviceJourney: ServiceJourney              # Detailed timetable information including stops and direction
    accumulatedDuration: int                    # Duration accumulated up to this leg
    delays: Dict[str, int]                      # Historical delay values per date
    bikeStationInfo: Any                        # Information about bicycle stations
    tripId: int                                 # Identifier of the public transport trip
    vehiclePositions: List[VehiclePositions]    # Actual vehicle position data attached to this leg

class TripPatternBase(TypedDict):
    """ Represents a complete trip consisting of multiple legs """
    legs: List[Leg]                             # List of legs in trip pattern
    aimedEndTime: str                           # Scheduled end time of the trip pattern

class TripPattern(TripPatternBase, total=False):
    """ Extended trip pattern """
    modes: List[str]                            # Modes used per segment
    polyInfo: List[Any]                         # Polyline info
    totalDuration: float                        # Total duration
    totalDistance: float                        # Total distance
    bikeDistance: float                         # Total cycling distance
    walkDistance: float                         # Total walking distance
    numOfTransfers: int                         # Total number of transfers
    originalLegs: List[Leg]                     # List of original legs
    tooLongWalkDistance: bool                   # Constraint flag walking distance exceeding maximal allowed distance
    tooLongBikeDistance: bool                   # Constraint flag cycling distance exceeding maximal allowed distance
    bikeSegmentFound: bool                      # Indicates present of cycling
    vehiclePositions: List[VehiclePositions]    # List of information about vehicle positions

class WaypointGroup(TypedDict):
    """ Grouping of consecutive waypoints that share the same transport mode """
    group: List[str]                            # Ordered list of waypoint coordinates
    mode: str                                   # Assigned transport mode for this waypoint group
    tripPatterns: List[TripPattern]             # Precomputed routing results for this group

class OtherDeparture(TypedDict):
    """ Used for processing GTFS data when searching for other departure options """
    trip_id: str                                # Unique GTFS trip identifier
    departure_time: str                         # Departure time
    direction: str                              # Tha final stop, trip headsign
    departure_dt: datetime                      # Parsed datetime object

class TripResponse(TypedDict):
    """ Represents a response object returned by an OTP trip query """
    tripPatterns: List[TripPattern]             # List of computed trip patterns
    nextPageCursor: str                         # Cursor used for pagination when requesting additional results

class OTPPublicQueryResponse(TypedDict):
    """ Wrapper structure for OTP public transport GraphQL response """
    trip: TripResponse                          # Main trip response object returned by OTP

class BikeRentalPlace(PlaceBase):
    """ Represents a bikesharing station returned by OTP """
    id: str                                     # Unique station identifier
    name: str                                   # Station name
    bikesAvailable: int                         # Number of bicycles currently available
    spacesAvailable: int                        # Number of free docking spaces
    allowDropoff: bool                          # Indicates whether bike drop-off is allowed at this station

class BikeStationNodeBase(TypedDict):
    """ Base structure for a ranked bike station candidate """
    distance: float                             # Distance from the reference location
    score: float                                # Computed ranking score used for station selection

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

class BikeStationNodeWrapper(TypedDict):
    """ Wrapper object for a bike station node """
    node: BikeStationNode                       # Bike station node data

class Results(TypedDict):
    """ Represents routing response results """
    tripPatterns: List[TripPattern]             # List of computed trip patterns
    active: bool                                # Indicates whether the routing result is active

# End of file route.py
