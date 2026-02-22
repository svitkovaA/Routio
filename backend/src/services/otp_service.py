"""
file: otp_service.py

Defines GraphQL queries for OpenTripPlanner and provides functions for
computing routes using public transport, bicycle, and walking modes. It handles
trip planning requests, and transforms raw OTP responses into internal
TripPattern structures. In addition to routing, it retrieves nearby
bike-sharing stations via OTP queries and enriches public transport legs with
additional data such as route colors, alternative departures, delay
information, and polyline-encoded geometries for map visualization.
"""

import asyncio
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple
from gql import gql
from gql.client import AsyncClientSession
import polyline                             # type: ignore[import-untyped]
from models.route import BikeStationNodeWrapper, Mode, OTPPublicQueryResponse, RoutingMode, TripPattern
from models.lissy import LissyShape, LissyShapes
from services.gtfs_gbfs_service import get_color, get_departures_via
from services.public_transport_service.lissy import get_delays, get_shape, get_shapes_cached, get_trip_id_by_time
from utils.planner_utils import combine_patterns

def public_transfer_max_number(count: int) -> int:
    """
    Retrieves maximal number of results taken into account based on total waypoint count
    
    Args:
        count: Number of waypoints on route

    Returns:
        Maximal number of results taken into account
    """
    print("function: public_transfer_max_number")

    # Threshold for maximum number of transfers based on total number of waypoints on the route
    pt_number_th = [0, 0, 5, 3, 2]

    if count >= len(pt_number_th):
        return pt_number_th[-1]
    
    return pt_number_th[count]

async def walk_bicycle_route(
    origin: str, 
    destination: str, 
    time_to_depart: datetime, 
    mode: RoutingMode,
    mode_speed: float,
    session: AsyncClientSession
) -> List[TripPattern]:
    """
    Compute walking or cycling route between two geographic points

    Args:
        origin: Origin coordinates in format lat,lon
        destination: Destination coordinates in format lat,lon
        time_to_depart: Departure time in ISO format
        mode: Direct travel mode to use
        session: Active asynchronous client session
    
    Returns:
        A list of trip patterns returned by OTP
    """
    print("function: walk_bicycle_route")

    # Parse origin and destination coordinates
    origin_lat, origin_lon = map(float, origin.split(','))
    destination_lat, destination_lon = map(float, destination.split(','))

    # Define GraphQL query for retrieving walking or cycling trips
    query = gql("""
        query trip($from: Location!, $to: Location!, $dateTime: DateTime, $modes: Modes, $walkSpeed: Float, $bikeSpeed: Float) {
            trip(
                from: $from
                to: $to
                dateTime: $dateTime
                modes: $modes
                walkSpeed: $walkSpeed
                bikeSpeed: $bikeSpeed
            ) {
                tripPatterns {
                    aimedEndTime
                    legs {
                        fromPlace {
                            latitude
                            longitude
                        }
                        toPlace {
                            latitude
                            longitude
                        }
                        mode
                        aimedStartTime
                        aimedEndTime
                        distance
                        duration
                        pointsOnLink {
                            points
                        }
                    }
                }
            }
        }
    """)

    # Prepare variables passed to the query
    variables: Dict[str, Any] = {
        "from": {
            "coordinates": {
                "latitude": origin_lat,
                "longitude": origin_lon
            }
        },
        "to": {
            "coordinates": {
                "latitude": destination_lat,
                "longitude": destination_lon
            }
        },
        "dateTime": time_to_depart.isoformat(),
        "modes": {
            "directMode": mode,
        },
        "walkSpeed": mode_speed / 3.6,
        "bikeSpeed": mode_speed / 3.6
    }

    try:
        # Execute the query asynchronously
        result = await session.execute(query, variable_values=variables)

        parsed = OTPPublicQueryResponse.model_validate(result)
    except:
        return []

    # Mark the first returned trip pattern if bicycle segment was requested
    if len(parsed.trip.tripPatterns) > 0:
        parsed.trip.tripPatterns[0].bikeSegmentFound = mode == "bicycle"

    return parsed.trip.tripPatterns

async def public_transport_route(
    waypoints: List[str], 
    time_to_depart: datetime, 
    arrive_by: bool,
    max_transfers: int, 
    modes: List[Mode], 
    session: AsyncClientSession, 
    num_of_waypoints: int,
    walk_speed: float,
    add_direct_mode: bool = False
) -> List[TripPattern]:
    """
    Computes public transport routes between multiple waypoints

    Args:
        waypoints: List of waypoint coordinates
        time_to_depart: Reference time in ISO format for departure or arrival
        arrive_by: True, if the routes are calculated for the arrival time, false if departure
        max_transfers: Maximum number of allowed transfers
        modes: List of allowed public transport modes
        session: Asynchronous GraphQL client session
        num_of_waypoints: Total number of waypoints in the route
        walk_speed: Walking speed in km/h
        add_direct_mode: If True, allows direct walking between waypoints as a fallback
    
    Returns:
        A list of trip patterns with information about delays and shapes
    """
    print("function: public_transport_route")

    # Define GraphQL query for retrieving trips using public transport
    query = gql("""
        query trip($from: Location!, $to: Location!, $dateTime: DateTime, $walkSpeed: Float, $maximumTransfers: Int, $pageCursor: String, $modes: Modes, $arriveBy: Boolean) {
            trip(
                from: $from
                to: $to
                dateTime: $dateTime
                walkSpeed: $walkSpeed
                maximumTransfers: $maximumTransfers
                pageCursor: $pageCursor
                modes: $modes
                arriveBy: $arriveBy
            ) {
                nextPageCursor
                tripPatterns {
                    aimedEndTime
                    legs {
                        mode
                        aimedStartTime
                        aimedEndTime
                        distance
                        duration
                        fromPlace {
                            latitude
                            longitude
                            name
                            quay {
                                id
                                name
                            }
                        }
                        toPlace {
                            latitude
                            longitude
                            name
                            quay {
                                id
                                name
                            }
                        }
                        line {
                            publicCode
                            name
                            id
                        }
                        serviceJourney {
                            quays {
                                id
                                name
                            }
                            passingTimes {
                                departure {
                                    time
                                }
                            }
                        }
                        pointsOnLink {
                            points
                        }
                    }
                }
            }
        }
    """)

    # Prepare variables passed to the query
    variables: Dict[str, Any] = {
        "walkSpeed": walk_speed / 3.6,
        "maximumTransfers": max_transfers,
        "pageCursor": "",
        "modes": {
            "accessMode": "foot",
            "egressMode": "foot",
            "transportModes": [{"transportMode": mode} for mode in modes]
        },
        "arriveBy": arrive_by
    }

    # Optionally allow a direct walking fallback between waypoints
    if add_direct_mode:
        variables["modes"]["directMode"] =  "foot"

    # Helper coroutine that executes a single public transport query
    async def public_route(local_variables: Dict[str, Any], time_to_depart: datetime) -> List[TripPattern]:
        local_variables["dateTime"] = time_to_depart.isoformat()
        attempt = 0
        trip_patterns = []
        
        # Number of retry if OTP returns no trip patterns
        while attempt < 10:
            try:
                # Query execution
                result = await session.execute(query, variable_values=local_variables)
                
                parsed = OTPPublicQueryResponse.model_validate(result)
            except:
                continue

            trip_patterns = parsed.trip.tripPatterns

            # Mark no trip patterns returned
            if len(trip_patterns) == 0:
                local_variables["pageCursor"] = parsed.trip.nextPageCursor
                attempt += 1
            else:
                break

        return trip_patterns

    trip_patterns: List[TripPattern] = []

    # Determine routing direction based on the arrive_by flag
    indices = list(reversed(range(len(waypoints) - 1))) if arrive_by else range(len(waypoints) - 1)

    first_iteration = True
    for i in indices:
        # Parse waypoint coordinates
        origin_lat, origin_lon = map(float, waypoints[i].split(','))
        destination_lat, destination_lon = map(float, waypoints[i + 1].split(','))

        # Create a local copy of variables for routing segment
        local_variables = deepcopy(variables)

        local_variables["from"] = {
            "coordinates": {
                "latitude": origin_lat,
                "longitude": origin_lon
            }
        }

        local_variables["to"] = {
            "coordinates": {
                "latitude": destination_lat,
                "longitude": destination_lon
                }
        }

        # Create routing tasks
        tasks = [
            public_route(
                local_variables, 
                pattern.legs[0].aimedStartTime if arrive_by else pattern.aimedEndTime
            )
            for pattern in trip_patterns
        ]

        # Initial routing step
        if tasks == []:
            tasks.append(public_route(local_variables, time_to_depart))

        # Execute routing queries concurrently
        results = await asyncio.gather(*tasks)

        new_results: List[List[TripPattern]] = []

        for res in results:
            # Group trip patterns by line and mode signature to eliminate results differentiated only in trip time
            patterns: Dict[str, List[TripPattern]] = {}
            for pattern in res:
                key = ""
                for leg in pattern.legs:
                    if leg.mode in ["foot", "bicycle"]:
                        key += f"-{leg.mode[0]}"
                    elif leg.line:
                        key += f"-{leg.line.publicCode}"

                patterns.setdefault(key, []).append(pattern)
            
            # Order trip_patterns by time based on routing mode
            new_trip_patterns: List[TripPattern] = []
            for item in patterns.values():
                if arrive_by:
                    best = max(item, key=lambda p: p.legs[0].aimedStartTime)
                else:
                    best = min(item, key=lambda p: p.aimedEndTime)
                new_trip_patterns.append(best)
            
            # Limit number of trip patterns to avoid combinatorial explosion
            truncated_trip_patterns = new_trip_patterns[:public_transfer_max_number(num_of_waypoints)]

            for pattern in truncated_trip_patterns:
                for leg in pattern.legs:
                    if leg.mode == "foot":
                        continue

                    # Add alternative departure options to public transport legs
                    if (leg.fromPlace and leg.fromPlace.quay and 
                        leg.toPlace and leg.toPlace.quay and 
                        leg.line
                    ):
                        departures = get_departures_via(
                            leg.fromPlace.quay.id.split(":", 1)[1], 
                            leg.toPlace.quay.id.split(":", 1)[1], 
                            leg.line.publicCode, 
                            leg.aimedStartTime
                        )
                        leg.otherOptions = departures
                        
                        # Attach trip_id when a matching departure is found
                        if departures.currentIndex and departures.currentIndex >= 0:
                            leg.tripId = departures.departures[departures.currentIndex].tripId
            
            new_results.append(truncated_trip_patterns)
        
        # Initialize or merge trip patterns across waypoint segments
        if trip_patterns == [] and first_iteration:
            trip_patterns = new_results[0]
        else:
            trip_patterns = combine_patterns(
                trip_patterns, 
                new_results, 
                arrive_by, 
                keep_without_connections=False
            )
        
        first_iteration = False
    
    # Load cached route shapes for the given date
    shape_by_route = await get_shapes_cached(time_to_depart.date())

    # Create list of the required shape ids
    needed_shape_ids: Set[int] = set()
    for pattern in trip_patterns:
        for leg in pattern.legs:
            # For public transport modes
            if leg.mode in ["bus", "tram", "rail", "metro", "water", "trolleybus"]:
                shape: LissyShapes | None = None
                stops = ""

                # Retrieve shape by public_code from cache
                if leg.line:
                    name = leg.line.publicCode
                    shape = shape_by_route.get(name)

                # Create stop_label
                if leg.serviceJourney:
                    stops = f"{leg.serviceJourney.quays[0].name} -> {leg.serviceJourney.quays[-1].name}"
                
                # Add shape_id to list of the required shape ids
                if shape:
                    for trip in shape.trips:
                        if trip.stops == stops:
                            needed_shape_ids.add(trip.shape_id)

    # Shape_id to shape_data map
    shape_id_to_data: Dict[int, LissyShape] = {}
    async def fetch_shape(shape_id: int) -> None:
        """
        Fetch shape data by shape_id

        Args:
            shape_id: Identifier of the shape
        """
        data = await get_shape(shape_id)
        if data:
            shape_id_to_data[shape_id] = data

    # Retrieve shape data
    await asyncio.gather(*(fetch_shape(sid) for sid in needed_shape_ids))

    # Get delays, shapes and route color for public transport legs
    for pattern in trip_patterns:
        for leg in pattern.legs:
            # For public transport
            if leg.mode in ["bus", "tram", "rail", "metro", "water", "trolleybus"]:
                if leg.line and leg.serviceJourney and leg.fromPlace and leg.toPlace:
                    name = leg.line.publicCode
                    stops = f"{leg.serviceJourney.quays[0].name} -> {leg.serviceJourney.quays[-1].name}"
                    shape = shape_by_route.get(name)
                    leg.serviceJourney.direction = leg.serviceJourney.quays[-1].name
                    
                    # Build stop_name to index map
                    quay_index_map = {quay.name: i for i, quay in enumerate(leg.serviceJourney.quays)}

                    # Find leg start and stop stop_name indexes
                    start_index = quay_index_map.get(leg.fromPlace.name if leg.fromPlace.name else "", -1)
                    stop_index = quay_index_map.get(leg.toPlace.name if leg.toPlace.name else "", -1)

                    # Valid indexes found
                    if start_index != -1 and stop_index != -1 and start_index <= stop_index:
                        leg.serviceJourney.quays = leg.serviceJourney.quays[start_index + 1:stop_index]
                        # Search trip id in cache, if delays available
                        trip_id = get_trip_id_by_time(
                            name, 
                            stops, 
                            leg.serviceJourney.passingTimes[0]["departure"].time
                        )

                        if trip_id:
                            delays = await get_delays(trip_id, start_index)
                            if delays:
                                leg.delays = delays

                    # Get route color from GTFS files if shape is not available
                    if shape is None:
                        color = get_color(name)
                        if color:
                            leg.color = color
                        continue
                    leg.color = f"#{shape.route_color}"

                    # Find shape_id for given stops
                    shapeID = next((trip.shape_id for trip in shape.trips if trip.stops == stops), None)
                    if shapeID is None:
                        continue

                    # Retrieve shape_data by id
                    shape_by_ID = shape_id_to_data.get(shapeID)
                    if shape_by_ID is None:
                        continue

                    # Find start and stop indexes in shape_data
                    stop_index_map: Dict[str, int] = {stop.stop_name: i for i, stop in enumerate(shape_by_ID.stops)}
                    from_idx = stop_index_map.get(leg.fromPlace.name if leg.fromPlace.name else "", -1)
                    to_idx = stop_index_map.get(leg.toPlace.name if leg.toPlace.name else "", -1)
                    if from_idx == -1 or to_idx == -1 or from_idx > to_idx:
                        continue

                    # Concat shapes in given stop range
                    coords: List[Tuple[float, float]] = []
                    for i in range(from_idx, to_idx):
                        coords.extend(shape_by_ID.coords[i])

                    # Encode coordinates to polyline
                    leg.pointsOnLink.points = polyline.encode(coords)

    return trip_patterns

async def nearest_bike_stations(
    lat: float,
    lon: float,
    session: AsyncClientSession,
    maximum_distance: int
) -> List[BikeStationNodeWrapper]:
    """
    Fetches the nearest bike stations to a given geographic location

    Args:
        lat: Latitude of the reference point
        lon: Longitude of the reference point
        session: Active asynchronous client session
        maximum_distance: Maximum search radius in meters

    Returns:
        A list of bike station nodes
    """
    print("function: nearest_bike_stations")
    
    # Define GraphQL query for retrieving nearby bike station nodes
    query = gql("""
        query nearestStations($latitude: Float!, $longitude: Float!, $maximum_distance: Float!) {
            nearest(
                latitude: $latitude,
                longitude: $longitude,
                maximumDistance: $maximum_distance,
                filterByPlaceTypes: [bicycleRent]
            ) {
                edges {
                    node {
                        distance
                        place {
                            latitude
                            longitude
                            ... on BikeRentalStation {
                                id
                                name
                                bikesAvailable
                                spacesAvailable
                                allowDropoff
                            }
                        }
                    }
                }
            }
        }
    """)
    
    # Prepare variables passed to the query
    variables: Dict[str, float] = {
        "latitude": lat,
        "longitude": lon,
        "maximum_distance": maximum_distance
    }

    try:
        # Execute the query asynchronously
        result = await session.execute(query, variable_values=variables)

        parsed = [
            BikeStationNodeWrapper.model_validate(node)
            for node in result["nearest"]["edges"]
        ]
    except:
        return []
    
    return parsed

# End of file otp_service.py
