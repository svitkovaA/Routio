from typing import Dict, Tuple, TypedDict, List, Any
from datetime import datetime

class Quay(TypedDict):
    id: str
    name: str

class PassingTime(TypedDict):
    time: str

class ServiceJourney(TypedDict):
    quays: List[Quay]
    direction: str
    passingTimes: List[Dict[str, PassingTime]]

class PointOnLink(TypedDict):
    points: str | List[str]

class Departure(TypedDict):
    departureTime: str
    direction: str

class OtherOptions(TypedDict):
    departures: List[Departure]
    currentIndex: int | None

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
    delays: Dict[str, int]
    bikeStationInfo: Any

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
    bikeSegmentFound: bool

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
    tripPatterns: List[TripPattern]

class OtherDeparture(TypedDict):
    trip_id: str
    departure_time: str
    direction: str
    departure_dt: datetime

class Departures(TypedDict):
    departures: List[Departure]
    currentIndex: None | int

class LissyTrips(TypedDict):
    id: int | None
    dep_time: str | None

class LissyDelayTrips(TypedDict):
    shape_id: str
    stops: str
    stopOrder: List[str]
    trips: List[LissyTrips]

class LissyAvailableRoute(TypedDict):
    route_short_name: str
    id: str

class RouteData(TypedDict):
    shape_id: str
    stopOrder: List[str]
    trips_by_time: Dict[str, int]

class LissyShapeStop(TypedDict):
    stop_name: str

class LissyShape(TypedDict):
    coords: List[List[Tuple[float, float]]]
    stops: List[LissyShapeStop]

class LissyShapeTrips(TypedDict):
    shape_id: int
    stops: str

class LissyShapes(TypedDict):
    route_short_name: str
    route_color: str
    trips: List[LissyShapeTrips]

class TripResponse(TypedDict):
    tripPatterns: List[TripPattern]
    nextPageCursor: str

class OTPPublicQueryResponse(TypedDict):
    trip: TripResponse

class BikeRentalPlace(PlaceBase):
    id: str
    name: str
    bikesAvailable: int
    spacesAvailable: int
    allowDropoff: bool

class BikeStationNodeBase(TypedDict):
    distance: float
    score: float

class BikeStationNode(BikeStationNodeBase):
    place: BikeRentalPlace

class BikeRackPlace(PlaceBase):
    name: str
    capacity: int

class BikeRackNode(BikeStationNodeBase):
    place: BikeRackPlace
    tags: Any

class BikeStationNodeWrapper(TypedDict):
    node: BikeStationNode
