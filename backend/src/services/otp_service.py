import asyncio
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple, cast
from gql import gql
from gql.client import AsyncClientSession
import polyline # type: ignore[import-untyped]
from models.types import LissyShape, LissyShapes, OTPPublicQueryResponse, TripPattern
from services.gtfs_gbfs_service import get_color, get_departures_via
from services.public_transport_service.lissy import get_delays, get_shape, get_shapes_cached, get_trip_id_by_time
from utils.planner_utils import combine_pt

def public_transfer_max_number(count: int) -> int:
    print("function: public_transfer_max_number")
    pt_number_th = [0, 0, 5, 3, 2]
    if count >= len(pt_number_th):
        return pt_number_th[-1]
    return pt_number_th[count]

async def walk_bicycle_route(
    origin: str, 
    destination: str, 
    time_to_depart: str, 
    mode: str, 
    session: AsyncClientSession
) -> List[TripPattern]: 
    print("function: walk_bicycle_route")
    origin_lat, origin_lon = map(float, origin.split(','))
    destination_lat, destination_lon = map(float, destination.split(','))

    query = gql("""
        query trip($from: Location!, $to: Location!, $dateTime: DateTime, $modes: Modes, $walkSpeed: Float) {
            trip(
                from: $from
                to: $to
                dateTime: $dateTime
                modes: $modes
                walkSpeed: $walkSpeed
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
        "dateTime": time_to_depart,
        "modes": {
            "directMode": mode,
        },
        "walkSpeed": 1.1
    }

    result = await session.execute(query, variable_values=variables)
    if len(result["trip"]["tripPatterns"]) > 0:
        result["trip"]["tripPatterns"][0]["bikeSegmentFound"] = mode == "bicycle"
    return result['trip']["tripPatterns"]

async def public_transport_route(
    waypoints: List[str], 
    time_to_depart: str, 
    arrive_by: bool,
    max_transfers: int, 
    modes: List[str], 
    session: AsyncClientSession, 
    num_of_waypoints: int, 
    add_direct_mode: bool = False
) -> List[TripPattern]:
    print("function: public_transport_route")
    query = gql("""
        query trip($from: Location!, $to: Location!, $via: [TripViaLocationInput!], $dateTime: DateTime, $walkSpeed: Float, $maximumTransfers: Int, $pageCursor: String, $modes: Modes, $arriveBy: Boolean) {
            trip(
                from: $from
                to: $to
                via: $via
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

    variables: Dict[str, Any] = {
        "walkSpeed": 1.1,
        "maximumTransfers": max_transfers,
        "pageCursor": "",
        "modes": {
            "accessMode": "foot",
            "egressMode": "foot",
            "transportModes": [{"transportMode": mode} for mode in modes]
        },
        "arriveBy": arrive_by
    }

    if add_direct_mode:
        variables["modes"]["directMode"] =  "foot"

    async def public_route(local_variables: Dict[str, Any], time_to_depart: str) -> List[TripPattern]:
        local_variables["dateTime"] = time_to_depart
        attempt = 0
        trip_patterns = []
        while attempt < 10:
            result = cast(OTPPublicQueryResponse, await session.execute(query, variable_values=local_variables))

            trip_patterns = result["trip"]["tripPatterns"]
            if len(trip_patterns) == 0:
                local_variables["pageCursor"] = result["trip"]["nextPageCursor"]
                attempt += 1
            else:
                break
        return trip_patterns

    trip_patterns: List[TripPattern] = []
    indices = list(reversed(range(len(waypoints) - 1))) if arrive_by else range(len(waypoints) - 1)
    first_iteration = True
    for i in indices:
        origin_lat, origin_lon = map(float, waypoints[i].split(','))
        destination_lat, destination_lon = map(float, waypoints[i + 1].split(','))
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
        tasks = [
            public_route(local_variables, pattern["legs"][0]["aimedStartTime"] if arrive_by else pattern["aimedEndTime"])
            for pattern in trip_patterns
        ]
        if tasks == []:
            tasks.append(public_route(local_variables, time_to_depart))

        results = await asyncio.gather(*tasks)

        new_results: List[List[TripPattern]] = []

        for res in results:
            patterns: Dict[str, List[TripPattern]] = {}
            for pattern in res:
                key = ""
                for leg in pattern["legs"]:
                    if leg["mode"] in ["foot", "bicycle"]:
                        key += f"-{leg["mode"][0]}"
                    elif "line" in leg:
                        key += f"-{leg["line"]["publicCode"]}"
                patterns.setdefault(key, []).append(pattern)
            
            new_trip_patterns: List[TripPattern] = []
            for item in patterns.values():
                if arrive_by:
                    best = max(item, key=lambda p: p["legs"][0]["aimedStartTime"])
                else:
                    best = min(item, key=lambda p: p["aimedEndTime"])
                new_trip_patterns.append(best)
            truncated_trip_patterns = new_trip_patterns[:public_transfer_max_number(num_of_waypoints)]
            for pattern in truncated_trip_patterns:
                for leg in pattern["legs"]:
                    if leg["mode"] == "foot":
                        continue
                    if "fromPlace" in leg and "quay" in leg["fromPlace"] and "toPlace" in leg and "quay" in leg["toPlace"] and "line" in leg:
                        departures = get_departures_via(leg["fromPlace"]["quay"]["id"].split(":", 1)[1], leg["toPlace"]["quay"]["id"].split(":", 1)[1], leg["line"]["publicCode"], leg["aimedStartTime"])
                        leg["otherOptions"] = departures
            new_results.append(truncated_trip_patterns)
        
        if trip_patterns == [] and first_iteration:
            trip_patterns = new_results[0]
        else:
            trip_patterns = combine_pt(trip_patterns, new_results, arrive_by, keep_base=False)
        first_iteration = False
    
    shape_by_route = await get_shapes_cached(datetime.fromisoformat(time_to_depart).date())

    needed_shape_ids: Set[int] = set()
    for pattern in trip_patterns:
        for leg in pattern["legs"]:
            if leg["mode"] in ["bus", "tram", "rail", "metro", "water", "trolleybus"]:
                shape: LissyShapes | None = None
                stops = ""
                if "line" in leg:
                    name = leg["line"]["publicCode"]
                    shape = shape_by_route.get(name)
                if "serviceJourney" in leg:
                    stops = f"{leg['serviceJourney']['quays'][0]['name']} -> {leg['serviceJourney']['quays'][-1]['name']}"
                if shape:
                    for trip in shape["trips"]:
                        if trip["stops"] == stops:
                            needed_shape_ids.add(trip["shape_id"])

    shape_id_to_data: Dict[int, LissyShape] = {}
    async def fetch_shape(shape_id: int) -> None:
        data = await get_shape(shape_id)
        if data:
            shape_id_to_data[shape_id] = data

    await asyncio.gather(*(fetch_shape(sid) for sid in needed_shape_ids))

    for pattern in trip_patterns:
        for leg in pattern["legs"]:
            if leg["mode"] in ["bus", "tram", "rail", "metro", "water", "trolleybus"]:
                if "line" in leg and "serviceJourney" in leg and "fromPlace" in leg and "toPlace" in leg:
                    name = leg["line"]["publicCode"]
                    stops = f"{leg['serviceJourney']['quays'][0]['name']} -> {leg['serviceJourney']['quays'][-1]['name']}"
                    shape = shape_by_route.get(name)
                    leg["serviceJourney"]["direction"] = leg["serviceJourney"]["quays"][-1]["name"]
                    
                    quay_index_map = {quay["name"]: i for i, quay in enumerate(leg['serviceJourney']['quays'])}
                    start_index = quay_index_map.get(leg["fromPlace"].get("name", ""), -1)
                    stop_index = quay_index_map.get(leg["toPlace"].get("name", ""), -1)
                    if start_index != -1 and stop_index != -1 and start_index <= stop_index:
                        leg["serviceJourney"]["quays"] = leg["serviceJourney"]["quays"][start_index + 1:stop_index]
                        # Search trip id in cache (if delays available)
                        trip_id = get_trip_id_by_time(name, stops, leg["serviceJourney"]["passingTimes"][0]["departure"]["time"])
                        if trip_id:
                            delays = await get_delays(trip_id, start_index)
                            if delays:
                                leg["delays"] = delays

                    if shape is None:
                        color = get_color(name)
                        if color:
                            leg["color"] = color
                        continue
                    leg["color"] = f"#{shape['route_color']}"

                    shapeID = next((trip["shape_id"] for trip in shape["trips"] if trip["stops"] == stops), None)
                    if shapeID is None:
                        continue

                    shape_by_ID = shape_id_to_data.get(shapeID)
                    if shape_by_ID is None:
                        continue

                    stop_index_map: Dict[str, int] = {stop["stop_name"]: i for i, stop in enumerate(shape_by_ID["stops"])}
                    from_idx = stop_index_map.get(leg["fromPlace"].get("name", ""), -1)
                    to_idx = stop_index_map.get(leg["toPlace"].get("name", ""), -1)
                    if from_idx == -1 or to_idx == -1 or from_idx > to_idx:
                        continue

                    coords: List[Tuple[float, float]] = []
                    for i in range(from_idx, to_idx):
                        coords.extend(shape_by_ID["coords"][i])

                    leg["pointsOnLink"]["points"] = polyline.encode(coords)

    return trip_patterns

async def nearest_bike_stations(lat: float, lon: float, session: AsyncClientSession, maximum_distance: int):
    print("function: nearest_bike_stations")
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
    
    variables: Dict[str, float] = {
        "latitude": lat,
        "longitude": lon,
        "maximum_distance": maximum_distance
    }

    result = await session.execute(query, variable_values=variables)
    return result["nearest"]["edges"]
