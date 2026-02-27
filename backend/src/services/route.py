"""
file: route.py

Routing engine of the application. It determines valid transport mode
combinations, dispatches routing tasks for public transport, walking, bicycle,
rental bicycle, public_bicycle and bicycle_public. Finally, recursively
composes partial results into computed TripPattern objects.
"""

import asyncio
from copy import deepcopy
from datetime import datetime
from itertools import product
from types import CoroutineType
from typing import Any, List, Tuple
from gql.client import AsyncClientSession
from models.route import RoutingMode, TripPattern, WaypointGroup
from models.route_data import LegPreferences, RouteData
from services.bicycle_public_route import bicycle_public_route
from services.bicycle_service.rental_bike_route import rental_bike_route
from services.bicycle_routes import group_walk_bicycle_route
from services.public_bicycle_route import public_bicycle_route
from services.public_transport_service.process_public_route import process_public_route
from utils.legs_processing import justify_time
from utils.geo import get_borderline_distance, haversine_distance_km
from utils.planner_utils import combine_patterns, contains_sublist, create_waypoint_groups

async def multimodal_route(
    waypoints: List[str],
    time_to_depart: datetime,
    data: RouteData,
    bike_segment_found: bool,
    session: AsyncClientSession,
    first_leg: bool = False
) -> List[TripPattern]:
    """
    The function computes total and segment distances, determines allowed transport modes per segment,
    retrieves all valid mode combinations, filters logically invalid combinations, executes routing tasks
    and filters results based on bicycle constraints

    Args:
        waypoints: Ordered list of coordinates
        time_to_depart: Departure time in ISO format
        data: Route preferences
        bike_segment_found: Indicates whether a bicycle segment has already been found
        session: Asynchronous GraphQL client session
        first_leg: Indicates whether current segment is the first on route

    Returns:
        List of TripPattern objects
    """
    print("function: multimodal_route")

    # Determine maximal distance on bicycle
    max_bike_distance = data.max_bike_distance if data.use_own_bike else data.max_bikesharing_distance

    # Compute borderline distance between walking and cycling for own bicycle
    if data.use_own_bike:
        borderline_distance = get_borderline_distance(
            data.bike_average_speed, 
            data.walk_speed, 
            data.bike_lock_time, 
            0.25
        )
    # Compute borderline distance between walking and cycling for shared bicycle
    else:
        borderline_distance = get_borderline_distance(
            data.bikesharing_average_speed, 
            data.walk_speed, 
            data.bikesharing_lock_time*2, 
            0.5
        )    
    
    total_distance = 0
    i = 0

    # Compute total route distance
    while i + 1 < len(waypoints):
        total_distance += haversine_distance_km(
            *map(float, waypoints[i].split(',')), 
            *map(float, waypoints[i + 1].split(','))
        )
        i += 1
    
    i = 0
    possible_modes: List[List[RoutingMode]] = []
    contains_bike = False

    # Determine possible modes per segment
    while i + 1 < len(waypoints):
        possible_modes.append([])
        distance = haversine_distance_km(
            *map(float, waypoints[i].split(',')), 
            *map(float, waypoints[i + 1].split(','))
        )
        
        # Walking is allowed if segment is within walk threshold
        if distance * 1.2 <= data.max_walk_distance:
            possible_modes[i].append("foot")
        
        # Public transport is allowed for medium/long distances
        if distance >= 0.5:
            possible_modes[i].append("walk_transit")
        
        # Bicycle logic only if not already used
        if not bike_segment_found and (first_leg or not data.use_own_bike):

            # Bicycle routing
            if borderline_distance <= distance and distance * 1.2 <= max_bike_distance:
                possible_modes[i].append("bicycle")
                contains_bike = True
            
            # Combination modes bicycle_public and public_bicycle
            if total_distance * 1.2 > max_bike_distance:
                contains_bike = True
                possible_modes[i].append("bicycle_public")

                if not data.use_own_bike:
                    possible_modes[i].append("public_bicycle")

        first_leg = False        
        i += 1
    
    # Compute mode combinations
    possible_mode_combinations = list(product(*possible_modes))

    tasks: List[CoroutineType[Any, Any, List[TripPattern]]] = []

    # Process all combinations
    for combination in possible_mode_combinations:
        preferences: List[LegPreferences] = []

        # Create list of preferences
        for mode in combination:
            preferences.append(LegPreferences(mode=mode, wait=0))

        waypoint_groups, _ = create_waypoint_groups(waypoints, preferences)

        # Limit number of bicycle segments to 1
        bike_count = sum(
            group.mode in ["bicycle", "bicycle_public", "public_bicycle"] 
            for group in waypoint_groups
        )
        
        if bike_count >= 2:
            continue
    
        # Filter logically invalid combinations
        if (contains_sublist(waypoint_groups, ["bicycle_public", "walk_transit"]) or 
            contains_sublist(waypoint_groups, ["walk_transit", "public_bicycle"])):
            continue

        print(combination)
        # if combination != ('foot',):
        #     continue

        tasks.append(route(waypoint_groups, time_to_depart, session, True, data, bike_segment_found))

    results = await asyncio.gather(*tasks)

    # Process results
    trip_patterns: List[TripPattern] = []
    for patterns in results:

        # Process computed trip patterns
        for pattern in patterns:
            bike_distance = 0

            # Compute bicycle distance
            if contains_bike:
                for leg in pattern.legs:
                    if leg.mode == "bicycle":
                        bike_distance += leg.distance

            # Validate maximal bicycle distance
            if bike_distance <= max_bike_distance * 1000 + 50:
                trip_patterns.append(pattern)

    return trip_patterns

async def route(
    waypoint_groups: List[WaypointGroup],
    time_to_depart: datetime,
    session: AsyncClientSession,
    multimodal: bool,
    data: RouteData,
    bike_segment_found: bool,
    first_leg: bool = False
) -> List[TripPattern]:
    """
    Precomputes bicycle and walking segments and first or last segment regardless of the mode
    according to arrive by mode

    Args:
        waypoint_groups: List of grouped waypoints with assigned transport mode
        time_to_depart: Departure time in ISO format
        session: Asynchronous GraphQL client session
        multimodal: Indicates whether the routing is part of multimodal planning
        data: Route preferences
        bike_segment_found: Indicates whether a bicycle segment has already been found
        first_leg: Indicates whether current segment is the first on route

    Returns:
        List of constructed TripPattern objects
    """
    print("function: route")

    # Determine bicycle configuration
    max_bike_distance = data.max_bike_distance if data.use_own_bike else data.max_bikesharing_distance
    bike_average_speed = data.bike_average_speed if data.use_own_bike else data.bikesharing_average_speed
    bike_lock_time = data.bike_lock_time if data.use_own_bike else data.bikesharing_lock_time

    tasks: List[CoroutineType[Any, Any, List[TripPattern]]] = []
    task_group_map: List[Tuple[WaypointGroup, CoroutineType[Any, Any, List[TripPattern]]]] = []

    # Process waypoint groups
    for i, group in enumerate(waypoint_groups):
        mode = group.mode
        waypoint_group = group.group

        # First or last segment in route according to arrive by mode
        if (i == 0 and not data.arrive_by) or (i == len(waypoint_groups) - 1 and data.arrive_by):
            # Public transport routing
            if mode == "walk_transit":
                task = process_public_route(
                    waypoint_group, 
                    time_to_depart, 
                    data.arrive_by, 
                    data.max_transfers, 
                    data.selected_modes, 
                    data.walk_speed, 
                    session
                )
                tasks.append(task)
                task_group_map.append((group, task))
            # Multimodal routing
            elif mode == "multimodal":
                task = multimodal_route(
                    waypoint_group, 
                    time_to_depart, 
                    data,
                    bike_segment_found, 
                    session, 
                    first_leg
                )
                tasks.append(task)
                task_group_map.append((group, task))
            # Bicycle_public routing
            elif mode == "bicycle_public":
                task = bicycle_public_route(
                    waypoint_group, 
                    time_to_depart, 
                    data.arrive_by, 
                    bike_lock_time, 
                    data.max_transfers, 
                    data.selected_modes, 
                    max_bike_distance,
                    bike_average_speed, 
                    data.use_own_bike, 
                    data.walk_speed, 
                    session
                )
                tasks.append(task)
                task_group_map.append((group, task))
            # Public_bicycle routing
            elif mode == "public_bicycle":
                task = public_bicycle_route(
                    waypoint_group, 
                    time_to_depart, 
                    data.arrive_by, 
                    data.bikesharing_lock_time, 
                    data.max_transfers, 
                    data.selected_modes, 
                    max_bike_distance,
                    bike_average_speed, 
                    data.use_own_bike, 
                    data.walk_speed, 
                    session
                )
                tasks.append(task)
                task_group_map.append((group, task))
        # Rental bicycle routing
        if mode == "bicycle" and not data.use_own_bike:
            task = rental_bike_route(
                waypoint_group, 
                time_to_depart,
                multimodal, 
                data.arrive_by, 
                data.bikesharing_lock_time,
                bike_average_speed, 
                data.walk_speed, 
                session
            )
            tasks.append(task)
            task_group_map.append((group, task))
        # Own bicycle and walking routing
        elif mode in ["bicycle", "foot"]:
            task = group_walk_bicycle_route(
                waypoint_group, 
                time_to_depart, 
                mode, 
                bike_average_speed, 
                data.walk_speed, 
                session, 
                bike_lock_time=data.bike_lock_time
            )
            tasks.append(task)
            task_group_map.append((group, task))
        first_leg = False

    results_list = await asyncio.gather(*tasks)

    # Attach computed trip patterns to their corresponding groups
    for (group, _), result in zip(task_group_map, results_list):
        group.tripPatterns.extend(result)
        
    # Reverse groups conditionally
    if data.arrive_by:
        waypoint_groups = list(reversed(waypoint_groups))

    # Routing engine
    results, _ = await recursive_planner(
        waypoint_groups, 
        time_to_depart, 
        data, 
        True, 
        bike_segment_found, 
        session
    )

    return results

async def recursive_planner(
    waypoint_groups: List[WaypointGroup],
    time_to_depart: datetime,
    data: RouteData,
    first_pt: bool,
    bike_segment_found: bool,
    session: AsyncClientSession
) -> Tuple[List[TripPattern], bool]:
    """
    Recursively plans route between given waypoints

    Args:
        waypoint_groups: List of grouped waypoints with assigned routing modes
        time_to_depart: Departure time in ISO format
        data: Route preferences
        first_pt: Indicates whether the first public transport segment has already been processed
        bike_segment_found: Indicates whether a bicycle segment has been found
        session: Asynchronous GraphQL client session

    Returns:
        Tuple (list of computed TripPattern objects, boolean indicating whether at least one valid route exists)
    """
    print("function: recursive_planner")

    # Determines bicycle configuration
    max_bike_distance = data.max_bike_distance if data.use_own_bike else data.max_bikesharing_distance
    bike_average_speed = data.bike_average_speed if data.use_own_bike else data.bikesharing_average_speed
    bike_lock_time = data.bike_lock_time if data.use_own_bike else data.bikesharing_lock_time

    trip_patterns: List[TripPattern] = []

    # Arrive by mode configuration
    leg_index = 0 if data.arrive_by else -1

    # Iterates over waypoint groups
    for i, group in enumerate(waypoint_groups):
        mode: RoutingMode = group.mode
        print("recursive_planner", i, mode)

        # Bicycle or walking mode
        if mode in ["foot", "bicycle"]:
            # Precomputed segment not found
            if not group.tripPatterns:
                return [], False
            
            # Adjust precomputed segment time
            justify_time(group.tripPatterns[0], time_to_depart, data.arrive_by)

            # Determines time to depart based on the arrive by mode
            if data.arrive_by:
                time_to_depart = group.tripPatterns[0].legs[0].aimedStartTime
            else:
                time_to_depart = group.tripPatterns[0].legs[-1].aimedEndTime

        # Precomputed segment for mode
        if (mode in ["walk_transit", "multimodal", "bicycle_public", "public_bicycle"] and 
            trip_patterns == [] and 
            group.tripPatterns
        ):

            base_patterns = group.tripPatterns

            # If not multimodal segment
            if mode != "multimodal":
                # Create pattern modes list
                for pattern in base_patterns:
                    pattern.modes = [mode] * (len(group.group) - 1)

            # Recursively plan rest of the route
            tasks = [
                recursive_planner(
                    waypoint_groups[i + 1:],
                    pattern.legs[leg_index].aimedStartTime if data.arrive_by else pattern.legs[leg_index].aimedEndTime,
                    data, 
                    False, 
                    pattern.bikeSegmentFound or bike_segment_found, 
                    session
                )
                for pattern in base_patterns
            ]

            results = await asyncio.gather(*tasks)

            # Process result
            results_t, validity_t = zip(*results)
            results = list(results_t)
            validity = list(validity_t)

            # Combine results
            return combine_patterns(
                base_patterns, 
                results, 
                data.arrive_by, 
                patterns_validity=validity
            ), any(validity)

        # Mode is not precomputed
        elif mode in ["walk_transit", "multimodal", "bicycle_public", "public_bicycle"]:
            # Public transport route
            if mode == "walk_transit":
                tasks = [
                    process_public_route(
                        group.group,
                        pattern.legs[leg_index].aimedStartTime if data.arrive_by else pattern.legs[leg_index].aimedEndTime,
                        data.arrive_by, 
                        data.max_transfers, 
                        data.selected_modes,
                        data.walk_speed, 
                        session
                    )
                    for pattern in trip_patterns
                ]

                # Routing first part of the subroute
                if len(tasks) == 0:
                    tasks.append(process_public_route(
                        group.group, 
                        time_to_depart, 
                        data.arrive_by, 
                        data.max_transfers, 
                        data.selected_modes, 
                        data.walk_speed, 
                        session
                    ))
            
            # Bicycle_public route
            elif mode == "bicycle_public":
                tasks = [
                    bicycle_public_route(
                        group.group,
                        pattern.legs[leg_index].aimedStartTime if data.arrive_by else pattern.legs[leg_index].aimedEndTime,
                        data.arrive_by, 
                        bike_lock_time, 
                        data.max_transfers, 
                        data.selected_modes,
                        max_bike_distance, 
                        bike_average_speed, 
                        data.use_own_bike, 
                        data.walk_speed, 
                        session
                    )
                    for pattern in trip_patterns
                ]

                # Routing first part of the subroute
                if len(tasks) == 0:
                    tasks.append(bicycle_public_route(
                        group.group, 
                        time_to_depart, 
                        data.arrive_by, 
                        bike_lock_time, 
                        data.max_transfers, 
                        data.selected_modes,
                        max_bike_distance, 
                        bike_average_speed, 
                        data.use_own_bike, 
                        data.walk_speed, 
                        session
                    ))
            
            # Public_bicycle route
            elif mode == "public_bicycle":
                tasks = [
                    public_bicycle_route(
                        group.group,
                        pattern.legs[leg_index].aimedStartTime if data.arrive_by else pattern.legs[leg_index].aimedEndTime,
                        data.arrive_by,
                        data.bikesharing_lock_time, 
                        data.max_transfers, 
                        data.selected_modes,
                        max_bike_distance, 
                        bike_average_speed, 
                        data.use_own_bike, 
                        data.walk_speed, 
                        session
                    )
                    for pattern in trip_patterns
                ]

                # Routing first part of the subroute
                if len(tasks) == 0:
                    tasks.append(public_bicycle_route(
                        group.group,
                        time_to_depart, 
                        data.arrive_by, 
                        data.bikesharing_lock_time, 
                        data.max_transfers, 
                        data.selected_modes, 
                        max_bike_distance, 
                        bike_average_speed, 
                        data.use_own_bike, 
                        data.walk_speed, 
                        session
                    ))
            
            # Multimodal route
            else:
                tasks = [
                    multimodal_route(
                        group.group, 
                        pattern.legs[leg_index].aimedStartTime if data.arrive_by else pattern.legs[leg_index].aimedEndTime,
                        data, 
                        bike_segment_found, 
                        session
                    )
                    for pattern in trip_patterns
                ]

                # Routing first part of the subroute
                if len(tasks) == 0:
                    tasks.append(multimodal_route(group.group, time_to_depart, data, bike_segment_found, session))
            
            results = await asyncio.gather(*tasks)
            
            # If not multimodal segment
            if mode != "multimodal":
                # Create pattern mode list
                for result in results:
                    for pattern in result:
                        pattern.modes = [mode] * (len(group.group) - 1)

            # Combine results
            trip_patterns = combine_patterns(
                trip_patterns, 
                results, 
                data.arrive_by, 
                first_pt, 
                keep_without_connections=False
            ) if len(trip_patterns) > 0 else results[0]

            # Recursively plan rest of the route
            tasks = [
                recursive_planner(
                    waypoint_groups[i + 1:],
                    pattern.legs[leg_index].aimedStartTime if data.arrive_by else pattern.legs[leg_index].aimedEndTime,
                    data, 
                    False,
                    pattern.bikeSegmentFound or bike_segment_found, 
                    session
                )
                for pattern in trip_patterns
            ]

            results_raw = await asyncio.gather(*tasks)

            # Process result
            validity: List[bool] = [len(waypoint_groups[i + 1:]) < 1]
            patterns: List[List[TripPattern]] = []
            if len(results_raw) > 0:
                validity = []
                for pat, valid in results_raw:
                    patterns.append(pat)
                    validity.append(valid)

            # Combine results
            return combine_patterns(
                trip_patterns, 
                patterns, 
                data.arrive_by, 
                patterns_validity=validity
            ), any(validity) and len(trip_patterns) > 0
        
        # Use cached results for bicycle or walking for empty trip patterns
        elif trip_patterns == []:
            # No results for bicycle or walking found
            if not group.tripPatterns:
                return [], False
            trip_patterns = deepcopy(group.tripPatterns)

        # Use cached results for bicycle or walking
        elif mode in ["foot", "bicycle"]:
            # No results for bicycle or walking found
            if not group.tripPatterns:
                return [], False
            
            # Add cached results to trip patterns
            for pattern in trip_patterns:
                # Arrive by mode
                if data.arrive_by:
                    new_legs = deepcopy(group.tripPatterns[0].legs)
                    new_legs.extend(deepcopy(pattern.legs))
                    pattern.legs = new_legs
                # Departure mode
                else:
                    pattern.legs.extend(deepcopy(group.tripPatterns[0].legs))
                    pattern.aimedEndTime = deepcopy(group.tripPatterns[0].legs[-1].aimedEndTime)

        # Create pattern mode list
        for pattern in trip_patterns:
            pattern.modes.extend([mode] * (len(group.group) - 1))

    return trip_patterns, True

# End of file route.py
