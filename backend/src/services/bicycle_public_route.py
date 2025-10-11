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

async def bicycle_public_route(waypoints: List[str], time_to_depart: str, arrive_by: bool, bike_lock_time: int, max_transfers: int, modes: List[str], max_bike_distance: float, bike_average_speed: float, use_own_bike: bool, session): 
    print("function: bicycle_public_route")
    i = 0
    bike_group = []
    distance = 0
    while i + 1 < len(waypoints) and distance * 1.2 <= max_bike_distance:
        bike_group.append(waypoints[i])
        distance += haversine_distance(*map(float, waypoints[i].split(',')), *map(float, waypoints[i + 1].split(',')))
        i += 1
    trip_patterns = []
    if i + 1 == len(waypoints) and distance * 1.2 <= max_bike_distance:
        return []
    else:
        distance_to_next = distance - max_bike_distance
        if len(bike_group) == 1:
            extra_distace = max_bike_distance
        else:
            extra_distace = haversine_distance(*map(float, waypoints[i - 1].split(',')), *map(float, waypoints[i].split(','))) - distance_to_next
        if len(bike_group) == 1 and extra_distace <= 1:
            return []
        if extra_distace <= 1 or distance_to_next <= 1:
            if extra_distace <= 1:
                print("extra distance")
                if use_own_bike:
                    result = await group_walk_bicycle_route(bike_group, time_to_depart, "bicycle", session, bicycle_public=True, bike_lock_time=bike_lock_time)
                else:
                    result = await rental_bike_route(bike_group, time_to_depart, True, arrive_by, bike_lock_time, session, bicycle_public=True, use_semicircle=True)
                for pattern in result:
                    walk_result = await walk_bicycle_route(f"{pattern["legs"][-2]["toPlace"]["latitude"]}, {pattern["legs"][-2]["toPlace"]["longitude"]}", bike_group[-1], pattern["aimedEndTime"], "foot", session)
                    if len(walk_result) > 0:
                        pattern["legs"].extend(walk_result[0]["legs"])
                        pattern["aimedEndTime"] = walk_result[0]["aimedEndTime"]
                        justify_time(pattern, time_to_depart, arrive_by)
                i -= 1
            else:
                print("distance to next")
                lat, lon = interpolate_point(*map(float, waypoints[i - 1].split(',')), *map(float, waypoints[i].split(',')), extra_distace * 0.8)
                bike_group.append(f"{lat}, {lon}")
                leg_index = -2
                if use_own_bike:
                    result = await group_walk_bicycle_route(bike_group, time_to_depart, "bicycle", session, bicycle_public=True, bike_lock_time=bike_lock_time)
                else:
                    result = await rental_bike_route(bike_group, time_to_depart, True, arrive_by, bike_lock_time, session, bicycle_public=True, use_semicircle=True)
                for pattern in result:
                    walk_result = await walk_bicycle_route(f"{pattern["legs"][leg_index]["toPlace"]["latitude"]}, {pattern["legs"][leg_index]["toPlace"]["longitude"]}", waypoints[i], pattern["aimedEndTime"], "foot", session)
                    if len(walk_result) > 0:
                        pattern["legs"].extend(walk_result[0]["legs"])
                        pattern["aimedEndTime"] = walk_result[0]["aimedEndTime"]
                        justify_time(pattern, time_to_depart, arrive_by)

            if len(result) == 0:
                return []

            if len(waypoints[i:]) < 2:
                trip_patterns.append(result[0])
            else:
                pt_result = await process_public_route(waypoints[i:], time_to_depart if arrive_by else result[0]["aimedEndTime"], arrive_by, max_transfers, modes, session)
                for pattern in result:
                    if len(pt_result) == 0:
                        trip_patterns.append(pattern)
                    for pt_pattern in pt_result:
                        new_pattern = deepcopy(pattern)
                        justify_time(new_pattern, pt_pattern["legs"][0]["aimedStartTime"], True)
                        new_pattern["legs"].extend(deepcopy(pt_pattern["legs"]))
                        new_pattern["aimedEndTime"] = deepcopy(pt_pattern["aimedEndTime"])
                        trip_patterns.append(new_pattern)
        else:
            print("vacsie")
            result = []
            factor = 0.9
            step = 0.05
            while len(result) == 0 and factor > 0.6:
                lat, lon = interpolate_point(*map(float, waypoints[i - 1].split(',')), *map(float, waypoints[i].split(',')), extra_distace * factor)
                new_waypoint = f"{lat}, {lon}"
                leg_index = -2
                if use_own_bike:
                    result = await group_walk_bicycle_route(bike_group + [new_waypoint], time_to_depart, "bicycle", session, bicycle_public=True, bike_lock_time=bike_lock_time)
                    if arrive_by and len(result) > 0:
                        justify_time(result[0], time_to_depart, True)
                else:
                    result = await rental_bike_route(bike_group + [new_waypoint], time_to_depart, False, arrive_by, bike_lock_time, session, bicycle_public=True, use_semicircle=True)
                temp_result = []
                for pattern in result:
                    bike_distance = 0
                    for leg in pattern["legs"]:
                        if leg["mode"] == "bicycle":
                            bike_distance += leg["distance"]
                    if bike_distance <= max_bike_distance * 1000 + 50:
                        temp_result.append(pattern)
                result = temp_result
                factor -= step
            tasks = [
                process_public_route(
                    [f"{pattern['legs'][leg_index]['toPlace']['latitude']}, {pattern['legs'][leg_index]['toPlace']['longitude']}", *waypoints[i:]],
                    time_to_depart if arrive_by else pattern["aimedEndTime"], arrive_by, max_transfers, modes, session
                )
                for pattern in result
            ]

            results = await asyncio.gather(*tasks)
            trip_patterns = combine_pt(result, results, False, first_pt=True, keep_base=False)
    return trip_patterns
