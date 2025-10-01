import asyncio
from copy import deepcopy
from typing import List
from services.bicycle_service.rental_bike_route import rental_bike_route
from services.bicycle_routes import group_walk_bicycle_route
from services.otp_service import walk_bicycle_route
from services.public_transport_service.public_transport_route import process_public_route
from utils.geo import haversine_distance, interpolate_point
from utils.legs_processing import justify_time
from utils.planner_utils import combine_pt

async def public_bicycle_route(waypoints: List[str], time_to_depart: str, arrive_by: bool, bike_lock_time: int, max_transfers: int, modes: List[str], max_bike_distance: float, bike_average_speed: float, use_own_bike: bool, session):
    print("function: public_bicycle_route")
    i = len(waypoints) - 1
    bike_group = []
    distance = 0
    while i > 0 and distance * 1.2 <= max_bike_distance:
        bike_group.insert(0, waypoints[i])
        distance += haversine_distance(*map(float, waypoints[i - 1].split(',')), *map(float, waypoints[i].split(',')))
        i -= 1
    trip_patterns = []
    if i == 0 and distance * 1.2 <= max_bike_distance:
        return []
    else:
        distance_to_next = distance - max_bike_distance
        if len(bike_group) == 1:
            extra_distace = max_bike_distance
        else:
            extra_distace = haversine_distance(*map(float, waypoints[i].split(',')), *map(float, waypoints[i + 1].split(','))) - distance_to_next    
        if len(bike_group) == 1 and extra_distace <= 1:
            return []
        if extra_distace <= 1 or distance_to_next <= 1:
            if extra_distace <= 1:
                print("extra_distace")
                if use_own_bike:
                    result = await group_walk_bicycle_route(bike_group, time_to_depart, "bicycle", session)
                    if arrive_by and len(result) > 0:
                        justify_time(result[0], time_to_depart, True)
                else:
                    result = await rental_bike_route(bike_group, time_to_depart, True, arrive_by, bike_lock_time, session, public_bicycle=True, use_semicircle=True)
                    for pattern in result:
                        walk_result = await walk_bicycle_route(bike_group[0], f"{pattern["legs"][1]["fromPlace"]["latitude"]}, {pattern["legs"][1]["fromPlace"]["longitude"]}", pattern["legs"][0]["aimedStartTime"], "foot", session)
                        if arrive_by and len(walk_result) > 0:
                            justify_time(walk_result[0], result[0]["legs"][0]["aimedStartTime"], True)
                        pattern["legs"][:0] = walk_result[0]["legs"]
                i += 1
            else:
                print("distance_to_next")
                lat, lon = interpolate_point(*map(float, waypoints[i + 1].split(',')), *map(float, waypoints[i].split(',')), extra_distace * 0.8)
                bike_group.insert(0, f"{lat}, {lon}")
                leg_index = 0
                if use_own_bike:
                    result = await group_walk_bicycle_route(bike_group, time_to_depart, "bicycle", session)
                    if arrive_by and len(result) > 0:  
                        justify_time(result[0], time_to_depart, True)  
                else:
                    result = await rental_bike_route(bike_group, time_to_depart, True, arrive_by, bike_lock_time, session, public_bicycle=True, use_semicircle=True)
                    leg_index = 1
                for pattern in result:
                    walk_result = await walk_bicycle_route(waypoints[i], f"{pattern["legs"][leg_index]["fromPlace"]["latitude"]}, {pattern["legs"][leg_index]["fromPlace"]["longitude"]}", pattern["legs"][0]["aimedStartTime"], "foot", session)
                    if arrive_by and len(walk_result) > 0:
                        justify_time(walk_result[0], result[0]["legs"][0]["aimedStartTime"], True)
                    pattern["legs"][:0] = walk_result[0]["legs"]
            
            if len(result) == 0:
                return []
            
            if len(waypoints[:i + 1]) < 2:
                trip_patterns.append(result[0])
            else:
                pt_result = await process_public_route(waypoints[:i + 1], result[0]["legs"][0]["aimedStartTime"] if arrive_by else time_to_depart, arrive_by, max_transfers, modes, session)
                for pattern in result:
                    if len(pt_result) == 0:
                        trip_patterns.append(pattern)
                    for pt_pattern in pt_result:
                        new_pattern = deepcopy(pattern)
                        justify_time(new_pattern, pt_pattern["aimedEndTime"], False)
                        new_pattern["legs"][:0] = deepcopy(pt_pattern["legs"])
                        trip_patterns.append(new_pattern)
        else:
            result = []
            factor = 0.9
            step = 0.05
            while len(result) == 0 and factor > 0.7:
                lat, lon = interpolate_point(*map(float, waypoints[i + 1].split(',')), *map(float, waypoints[i].split(',')), extra_distace * factor)
                new_waypoint = f"{lat}, {lon}"
                leg_index = 0
                if use_own_bike:
                    result = await group_walk_bicycle_route([new_waypoint] + bike_group, time_to_depart, "bicycle", session)
                    if arrive_by and len(result) > 0:
                        justify_time(result[0], time_to_depart, True)
                else:
                    result = await rental_bike_route([new_waypoint] + bike_group, time_to_depart, True, arrive_by, bike_lock_time, session, public_bicycle=True, use_semicircle=True)
                    leg_index = 1
                temp_result = []
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
            tasks = [
                process_public_route(
                    [*waypoints[:i + 1], f"{pattern['legs'][leg_index]['fromPlace']['latitude']}, {pattern['legs'][leg_index]['fromPlace']['longitude']}"],
                    pattern["legs"][0]["aimedStartTime"] if arrive_by else time_to_depart, arrive_by, max_transfers, modes, session
                )
                for pattern in result
            ]

            results = await asyncio.gather(*tasks)
            trip_patterns = combine_pt(result, results, True, first_pt=True, keep_base=False, combination=True)

    return trip_patterns
