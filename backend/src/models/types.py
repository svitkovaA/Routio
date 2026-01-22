from typing import TypedDict, List, Any
from datetime import datetime

class Quay(TypedDict):
    id: str
    name: str

class ServiceJourney(TypedDict):
    quays: List[Quay]
    direction: str

class PointOnLink(TypedDict):
    points: str | List[str]

class Departure(TypedDict):
    departureTime: str
    direction: str

class OtherOptions(TypedDict):
    departures: List[Departure]
    currentIndex: int

class Line(TypedDict):
    publicCode: str

class PlaceBase(TypedDict):
    latitude: float
    longitude: float

class Place(PlaceBase, total=False):
    name: str
    quay: Quay

class LegBase(TypedDict):
    mode: str
    aimedStartTime: str
    aimedEndTime: str
    distance: float
    duration: int
    pointsOnLink: PointOnLink

class Leg(LegBase, total=False):
    fromPlace: Place
    toPlace: Place
    color: str
    otherOptions: OtherOptions
    walkMode: bool
    line: Line
    serviceJourney: ServiceJourney
    accumulatedDuration: int

class TripPatternBase(TypedDict):
    legs: List[Leg]
    aimedEndTime: str

class TripPattern(TripPatternBase, total=False):
    modes: List[str]
    polyInfo: List[Any]
    totalDuration: float
    totalDistance: float
    bikeDistance: float
    walkDistance: float
    numOfTransfers: int
    originalLegs: List[Leg]
    tooLongWalkDistance: bool
    tooLongBikeDistance: bool

class Suggestion(TypedDict):
    name: str
    type: str
    country: str
    city: str
    street: str | None
    lat: float
    lon: float

class WaypointGroup(TypedDict):
    group: List[str]
    mode: str

class OtherDeparture(TypedDict):
    trip_id: str
    departure_time: str
    direction: str
    departure_dt: datetime

class Departures(TypedDict):
    departures: List[Departure]
    currentIndex: None | int
