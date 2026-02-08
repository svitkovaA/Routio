import asyncio
from copy import deepcopy
from types import CoroutineType
from typing import Any, List
from models.types import TripPattern
from services.bicycle_service.rental_bike_route import rental_bike_route
from services.bicycle_routes import group_walk_bicycle_route
from services.otp_service import walk_bicycle_route
from services.public_transport_service.public_transport_route import process_public_route
from utils.geo import haversine_distance, interpolate_point
from utils.legs_processing import justify_time
from utils.planner_utils import combine_pt
from gql.client import AsyncClientSession

async def public_bicycle_route(
    waypoints: List[str], 
    time_to_depart: str, 
    arrive_by: bool, 
    bike_lock_time: int, 
    max_transfers: int, 
    modes: List[str], 
    max_bike_distance: float, 
    bike_average_speed: float, 
    use_own_bike: bool, 
    walk_speed: float,
    session: AsyncClientSession
) -> List[TripPattern]:
    print("function: public_bicycle_route")
    i = len(waypoints) - 1
    bike_group: List[str] = []
    distance = 0
    while i > 0 and distance * 1.2 <= max_bike_distance:
        bike_group.insert(0, waypoints[i])
        distance += haversine_distance(*map(float, waypoints[i - 1].split(',')), *map(float, waypoints[i].split(',')))
        i -= 1
    trip_patterns: List[TripPattern] = []
    if i == 0 and distance * 1.2 <= max_bike_distance:
        return []
    else:
        distance_to_next = distance - max_bike_distance
        if len(bike_group) == 1:
            extra_distance = max_bike_distance
        else:
            extra_distance = haversine_distance(*map(float, waypoints[i].split(',')), *map(float, waypoints[i + 1].split(','))) - distance_to_next    
        if len(bike_group) == 1 and extra_distance <= 1:
            return []
        if extra_distance <= 1 or distance_to_next <= 1:
            if extra_distance <= 1:
                print("extra_distance")
                if use_own_bike:
                    result = await group_walk_bicycle_route(bike_group, time_to_depart, "bicycle", bike_average_speed, walk_speed, session)
                    if arrive_by and len(result) > 0:
                        justify_time(result[0], time_to_depart, True)
                else:
                    result = await rental_bike_route(bike_group, time_to_depart, True, arrive_by, bike_lock_time, bike_average_speed, walk_speed, session, public_bicycle=True, use_semicircle=True)
                    for pattern in result:
                        if "fromPlace" not in pattern["legs"][1]:
                            continue
                        walk_result = await walk_bicycle_route(bike_group[0], f"{pattern["legs"][1]["fromPlace"]["latitude"]}, {pattern["legs"][1]["fromPlace"]["longitude"]}", pattern["legs"][0]["aimedStartTime"], "foot", walk_speed, session)
                        if arrive_by and len(walk_result) > 0:
                            justify_time(walk_result[0], result[0]["legs"][0]["aimedStartTime"], True)
                        pattern["legs"][:0] = walk_result[0]["legs"]
                i += 1
            else:
                print("distance_to_next")
                lat1, lon1 = map(float, waypoints[i + 1].split(','))
                lat2, lon2 = map(float, waypoints[i].split(','))
                lat, lon = interpolate_point(lat1, lon1, lat2, lon2, extra_distance * 0.8)
                bike_group.insert(0, f"{lat}, {lon}")
                leg_index = 0
                if use_own_bike:
                    result = await group_walk_bicycle_route(bike_group, time_to_depart, "bicycle", bike_average_speed, walk_speed, session)
                    if arrive_by and len(result) > 0:  
                        justify_time(result[0], time_to_depart, True)  
                else:
                    result = await rental_bike_route(bike_group, time_to_depart, True, arrive_by, bike_lock_time, bike_average_speed, walk_speed, session, public_bicycle=True, use_semicircle=True)
                    leg_index = 1
                for pattern in result:
                    fromPlace = pattern["legs"][leg_index].get("fromPlace", None)
                    if fromPlace is None:
                        continue
                    walk_result = await walk_bicycle_route(waypoints[i], f"{fromPlace["latitude"]}, {fromPlace["longitude"]}", pattern["legs"][0]["aimedStartTime"], "foot", walk_speed, session)
                    if arrive_by and len(walk_result) > 0:
                        justify_time(walk_result[0], result[0]["legs"][0]["aimedStartTime"], True)
                    pattern["legs"][:0] = walk_result[0]["legs"]
            
            if len(result) == 0:
                return []
            
            if len(waypoints[:i + 1]) < 2:
                trip_patterns.append(result[0])
            else:
                pt_result = await process_public_route(waypoints[:i + 1], result[0]["legs"][0]["aimedStartTime"] if arrive_by else time_to_depart, arrive_by, max_transfers, modes, walk_speed, session)
                for pattern in result:
                    if len(pt_result) == 0:
                        trip_patterns.append(pattern)
                    for pt_pattern in pt_result:
                        new_pattern = deepcopy(pattern)
                        justify_time(new_pattern, pt_pattern["aimedEndTime"], False)
                        new_pattern["legs"][:0] = deepcopy(pt_pattern["legs"])
                        trip_patterns.append(new_pattern)
        else:
            result: List[TripPattern] = []
            factor = 0.9
            step = 0.05
            leg_index = 0
            while len(result) == 0 and factor > 0.6:
                lat1, lon1 = map(float, waypoints[i + 1].split(','))
                lat2, lon2 = map(float, waypoints[i].split(','))
                lat, lon = interpolate_point(lat1, lon1, lat2, lon2, extra_distance * factor)
                new_waypoint = f"{lat}, {lon}"
                leg_index = 0
                if use_own_bike:
                    result = await group_walk_bicycle_route([new_waypoint] + bike_group, time_to_depart, "bicycle", bike_average_speed, walk_speed, session)
                    if arrive_by and len(result) > 0:
                        justify_time(result[0], time_to_depart, True)
                else:
                    result = await rental_bike_route([new_waypoint] + bike_group, time_to_depart, True, arrive_by, bike_lock_time, bike_average_speed, walk_speed, session, public_bicycle=True, use_semicircle=True)
                    leg_index = 1
                temp_result: List[TripPattern] = []
                for pattern in result:
                    bike_distance = 0
                    for leg in pattern["legs"]:
                        if leg["mode"] == "bicycle":
                            bike_distance += leg["distance"]
                    if bike_distance <= max_bike_distance * 1000:
                        temp_result.append(pattern)
                result = temp_result
                factor -= step

            print("vacsie")
            tasks: List[CoroutineType[Any, Any, List[TripPattern]]] = []
            for pattern in result:
                fromPlace = pattern['legs'][leg_index].get('fromPlace', None)
                if fromPlace is None:
                    continue
                tasks.append(
                    process_public_route(
                        [*waypoints[:i + 1], f"{fromPlace['latitude']}, {fromPlace['longitude']}"],
                        pattern["legs"][0]["aimedStartTime"] if arrive_by else time_to_depart, arrive_by, max_transfers, modes, walk_speed, session
                    )
                )

            results = await asyncio.gather(*tasks)
            trip_patterns = combine_pt(result, results, True, first_pt=True, keep_base=False, combination=True)

    return trip_patterns

# End of file public_bicycle_route.py
