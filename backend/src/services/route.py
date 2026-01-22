import asyncio
from copy import deepcopy
from itertools import product
from utils.legs_processing import justify_time
from models.route_data import LegPreferences, RouteData
from services.bicycle_public_route import bicycle_public_route
from services.bicycle_service.rental_bike_route import rental_bike_route
from services.bicycle_routes import group_walk_bicycle_route
from services.public_bicycle_route import public_bicycle_route
from services.public_transport_service.public_transport_route import process_public_route
from utils.geo import get_borderline_distance, haversine_distance
from utils.planner_utils import combine_pt, contains_sublist, create_waypoint_groups

async def multimodal_route(waypoints, time_to_depart: str, data: RouteData, bike_segment_found: bool, session, first_leg: bool = False):
    print("function: multimodal_route")
    max_bike_distance = data.max_bike_distance if data.use_own_bike else data.max_bikesharing_distance
    possible_modes = []
    total_distance = 0
    if data.use_own_bike:
        borderline_distance = get_borderline_distance(data.bike_average_speed, data.walk_average_speed, data.bike_lock_time, 0.25)
    else:
        borderline_distance = get_borderline_distance(data.bikesharing_average_speed, data.walk_average_speed, data.bikesharing_lock_time*2, 0.5)    
    i = 0
    while i + 1 < len(waypoints):
        total_distance += haversine_distance(*map(float, waypoints[i].split(',')), *map(float, waypoints[i + 1].split(',')))
        i += 1
    i = 0
    contains_bike = False
    while i + 1 < len(waypoints):
        possible_modes.append([])
        distance = haversine_distance(*map(float, waypoints[i].split(',')), *map(float, waypoints[i + 1].split(',')))
        if distance * 1.2 <= data.max_walk_distance:
            possible_modes[i].append("foot")
        if distance >= 0.5:
            possible_modes[i].append("walk_transit")
        if not bike_segment_found and (first_leg or not data.use_own_bike):
            if borderline_distance <= distance and distance * 1.2 <= max_bike_distance:
                possible_modes[i].append("bicycle")
                contains_bike = True
            if total_distance * 1.2 > max_bike_distance:
                contains_bike = True
                possible_modes[i].append("bicycle_walk_transit")
                if not data.use_own_bike:
                    possible_modes[i].append("walk_transit_bicycle")
        first_leg = False
                    
        i += 1
    possible_mode_combinations = list(product(*possible_modes))

    tasks = []
    for combination in possible_mode_combinations:
        preferences = []
        for mode in combination:
            preferences.append(LegPreferences(mode=mode, wait=0))
        waypoint_groups, _ = create_waypoint_groups(waypoints, preferences)

        bike_count = sum(group["mode"] in ["bicycle", "bicycle_walk_transit", "walk_transit_bicycle"] for group in waypoint_groups)
        if bike_count >= 2:
            continue
    
        if contains_sublist(waypoint_groups, ["bicycle_walk_transit", "walk_transit"]) or contains_sublist(waypoint_groups, ["walk_transit", "walk_transit_bicycle"]):
            continue

        print(combination)
        # if combination != ('walk_transit_bicycle', 'walk_transit'):
        #     continue
        tasks.append(route(waypoint_groups, time_to_depart, session, True, data, bike_segment_found))

    results = await asyncio.gather(*tasks)

    trip_patterns = []
    for patterns in results:
        for pattern in patterns:
            bike_distance = 0
            if contains_bike:
                for leg in pattern["legs"]:
                    if leg["mode"] == "bicycle":
                        bike_distance += leg["distance"]
            print(bike_distance,  max_bike_distance * 1000)
            if bike_distance <= max_bike_distance * 1000 + 50:
                trip_patterns.append(pattern)
    return trip_patterns

async def route(waypoint_groups, time_to_depart: str, session, multimodal: bool, data: RouteData, bike_segment_found: bool, first_leg: bool = False):
    print("function: route")
    max_bike_distance = data.max_bike_distance if data.use_own_bike else data.max_bikesharing_distance
    bike_average_speed = data.bike_average_speed if data.use_own_bike else data.bikesharing_average_speed
    bike_lock_time = data.bike_lock_time if data.use_own_bike else data.bikesharing_lock_time
    tasks = []
    task_group_map = []
    for i, group in enumerate(waypoint_groups):
        mode = group["mode"]
        waypoint_group = group["group"]
        if (i == 0 and not data.arrive_by) or (i == len(waypoint_groups) - 1 and data.arrive_by):
            if mode == "walk_transit":
                task = process_public_route(waypoint_group, time_to_depart, data.arrive_by, data.max_transfers, data.selected_modes, session)
                tasks.append(task)
                task_group_map.append((group, task))
            elif mode == "transit,bicycle,walk":
                task = multimodal_route(waypoint_group, time_to_depart, data, bike_segment_found, session, first_leg)
                tasks.append(task)
                task_group_map.append((group, task))
            elif mode == "bicycle_walk_transit":
                task = bicycle_public_route(waypoint_group, time_to_depart, data.arrive_by, bike_lock_time, data.max_transfers, data.selected_modes, max_bike_distance, bike_average_speed, data.use_own_bike, session)
                tasks.append(task)
                task_group_map.append((group, task))
            elif mode == "walk_transit_bicycle":
                task = public_bicycle_route(waypoint_group, time_to_depart, data.arrive_by, data.bikesharing_lock_time, data.max_transfers, data.selected_modes, max_bike_distance, bike_average_speed, data.use_own_bike, session)
                tasks.append(task)
                task_group_map.append((group, task))
        if mode == "bicycle" and not data.use_own_bike:
            task = rental_bike_route(waypoint_group, time_to_depart, multimodal, data.arrive_by, data.bikesharing_lock_time, session)
            tasks.append(task)
            task_group_map.append((group, task))
        elif mode in ["bicycle", "foot"]:
            task = group_walk_bicycle_route(waypoint_group, time_to_depart, mode, session, bike_lock_time=data.bike_lock_time)
            tasks.append(task)
            task_group_map.append((group, task))
        first_leg = False

    results_list = await asyncio.gather(*tasks)
    for (group, _), result in zip(task_group_map, results_list):
        if "tripPatterns" not in group:
            group["tripPatterns"] = []
        group["tripPatterns"].extend(result)
        
    if data.arrive_by:
        waypoint_groups = list(reversed(waypoint_groups))
    results, _ = await recursive_planner(waypoint_groups, time_to_depart, data, True, bike_segment_found, session)
    return results

async def recursive_planner(waypoint_groups, time_to_depart: str, data: RouteData, first_pt: bool, bike_segment_found: bool, session):
    print("function: recursive_planner")
    max_bike_distance = data.max_bike_distance if data.use_own_bike else data.max_bikesharing_distance
    bike_average_speed = data.bike_average_speed if data.use_own_bike else data.bikesharing_average_speed
    bike_lock_time = data.bike_lock_time if data.use_own_bike else data.bikesharing_lock_time
    trip_patterns = []
    leg_index = 0 if data.arrive_by else -1
    leg_time = "aimedStartTime" if data.arrive_by else "aimedEndTime"

    for i, group in enumerate(waypoint_groups):
        mode = group["mode"]
        print("recursive_planner", i, mode)

        if mode in ["foot", "bicycle"]:
            if not group.get("tripPatterns"):
                return [], False
            justify_time(group["tripPatterns"][0], time_to_depart, data.arrive_by)
            if data.arrive_by:
                time_to_depart = group["tripPatterns"][0]["legs"][0]["aimedStartTime"]
            else:
                time_to_depart = group["tripPatterns"][0]["legs"][-1]["aimedEndTime"]

        if mode in ["walk_transit", "transit,bicycle,walk", "bicycle_walk_transit", "walk_transit_bicycle"] and trip_patterns == [] and group.get("tripPatterns"):
            if not group.get("tripPatterns"):
                return [], False
            base_patterns = group["tripPatterns"]
            if mode != "transit,bicycle,walk":
                for pattern in base_patterns:
                    pattern["modes"] = [mode] * (len(group["group"]) - 1)
            tasks = [
                recursive_planner(
                    waypoint_groups[i + 1:],
                    pattern["legs"][leg_index][leg_time],
                    data, False, pattern.get("bikeSegmentFound", False) or bike_segment_found, session
                )
                for pattern in base_patterns
            ]
            results = await asyncio.gather(*tasks)
            results, validity = zip(*results)
            return combine_pt(base_patterns, results, data.arrive_by, validity=validity), any(validity)

        elif mode in ["walk_transit", "transit,bicycle,walk", "bicycle_walk_transit", "walk_transit_bicycle"]:
            if mode == "walk_transit":
                tasks = [
                    process_public_route(
                        group["group"],
                        pattern["legs"][leg_index][leg_time],
                        data.arrive_by, data.max_transfers, data.selected_modes, session
                    )
                    for pattern in trip_patterns
                ]
                if len(tasks) == 0:
                    tasks.append(process_public_route(group["group"], time_to_depart, data.arrive_by, data.max_transfers, data.selected_modes, session))
            elif mode == "bicycle_walk_transit":
                tasks = [
                    bicycle_public_route(
                        group["group"],
                        pattern["legs"][leg_index][leg_time],
                        data.arrive_by, bike_lock_time, data.max_transfers, data.selected_modes, max_bike_distance, bike_average_speed, data.use_own_bike, session
                    )
                    for pattern in trip_patterns
                ]
                if len(tasks) == 0:
                    tasks.append(bicycle_public_route(group["group"], time_to_depart, data.arrive_by, bike_lock_time, data.max_transfers, data.selected_modes, max_bike_distance, bike_average_speed, data.use_own_bike, session))
            elif mode == "walk_transit_bicycle":
                tasks = [
                    public_bicycle_route(
                        group["group"],
                        pattern["legs"][leg_index][leg_time],
                        data.arrive_by, data.bikesharing_lock_time, data.max_transfers, data.selected_modes, max_bike_distance, bike_average_speed, data.use_own_bike, session
                    )
                    for pattern in trip_patterns
                ]
                if len(tasks) == 0:
                    tasks.append(public_bicycle_route(group["group"], time_to_depart, data.arrive_by, data.bikesharing_lock_time, data.max_transfers, data.selected_modes, max_bike_distance, bike_average_speed, data.use_own_bike, session))
            else:
                tasks = [
                    multimodal_route(
                        group["group"], pattern["legs"][leg_index][leg_time],
                        data, bike_segment_found, session
                    )
                    for pattern in trip_patterns
                ]
                if len(tasks) == 0:
                    tasks.append(multimodal_route(group["group"], time_to_depart, data, bike_segment_found, session))
            results = await asyncio.gather(*tasks)
            
            if mode != "transit,bicycle,walk":
                for result in results:
                    for pattern in result:
                        pattern["modes"] = [mode] * (len(group["group"]) - 1)

            trip_patterns = combine_pt(trip_patterns, results, data.arrive_by, first_pt, keep_base=False) if len(trip_patterns) > 0 else results[0]

            tasks = [
                recursive_planner(
                    waypoint_groups[i + 1:],
                    pattern["legs"][leg_index][leg_time],
                    data, False, pattern.get("bikeSegmentFound", False) or bike_segment_found, session
                )
                for pattern in trip_patterns
            ]
            results = await asyncio.gather(*tasks)
            validity = [len(waypoint_groups[i + 1:]) < 1]
            if len(results) > 0:
                results, validity = zip(*results)
            return combine_pt(trip_patterns, results, data.arrive_by, validity=validity), any(validity) and len(trip_patterns) > 0
        
        elif trip_patterns == []:
            if not group.get("tripPatterns"):
                return [], False
            trip_patterns = deepcopy(group["tripPatterns"])

        elif mode in ["foot", "bicycle"]:
            if not group.get("tripPatterns"):
                return [], False
            for pattern in trip_patterns:
                if data.arrive_by:
                    new_legs = deepcopy(group["tripPatterns"][0]["legs"])
                    new_legs.extend(deepcopy(pattern["legs"]))
                    pattern["legs"] = new_legs
                else:
                    pattern["legs"].extend(deepcopy(group["tripPatterns"][0]["legs"]))
                    pattern["aimedEndTime"] = deepcopy(group["tripPatterns"][0]["legs"][-1]["aimedEndTime"])

        for pattern in trip_patterns:
            if "modes" not in pattern:
                pattern["modes"] = []
            pattern["modes"].extend([mode] * (len(group["group"]) - 1))

    return trip_patterns, True
