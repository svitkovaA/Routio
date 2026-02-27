"""
file: bicycle_public_route.py

File implements the bicycle_public algorithm. The first part of the route,
between the two waypoints, is computed using a bicycle, while the second part
is computed using public transport. Both own a bicycle, and a rental bicycle
can be used in this algorithm. When using one's own bicycle, bicycle racks are
used for planning the trip, while when using a rental bicycle, origin and
destination bicycle stations must be found.
"""

import asyncio
from copy import deepcopy
from datetime import datetime
from types import CoroutineType
from typing import Any, List
from gql.client import AsyncClientSession
from models.route import Mode, TripPattern
from services.bicycle_service.rental_bike_route import rental_bike_route
from services.bicycle_routes import group_walk_bicycle_route
from services.otp_service import walk_bicycle_route
from services.public_transport_service.process_public_route import process_public_route
from utils.geo import haversine_distance_km, interpolate_point
from utils.legs_processing import justify_time
from utils.planner_utils import combine_patterns

async def bicycle_public_route(
    waypoints: List[str], 
    time_to_depart: datetime, 
    arrive_by: bool, 
    bike_lock_time: int, 
    max_transfers: int, 
    modes: List[Mode], 
    max_bike_distance: float, 
    bike_average_speed: float, 
    use_own_bike: bool,
    walk_speed: float,
    session: AsyncClientSession
) -> List[TripPattern]:
    """
    Computes route between given waypoints using bicycle_public algorithm

    Args:
        waypoints: Ordered list of coordinates
        time_to_depart: Departure time in ISO format
        arrive_by: If true, routing is performed in arrive by mode
        bike_lock_time: Time in seconds required to lock or unlock the bicycle
        max_transfers: Maximum allowed number of public transport transfers
        modes: List of allowed public transport modes
        max_bike_distance: Maximum allowed cycling distance
        bike_average_speed: Average cycling speed
        use_own_bike: If true, the user is using an own bicycle, shared bicycle otherwise
        walk_speed: Walking speed
        session: Asynchronous GraphQL client session
        
    Returns: 
        List of TripPattern objects
    """
    print("function: bicycle_public_route")
    i = 0
    bike_group: List[str] = []
    distance = 0

    # Create waypoint group to not exceed maximal allowed bicycle distance
    while i + 1 < len(waypoints) and distance * 1.2 <= max_bike_distance:
        bike_group.append(waypoints[i])
        distance += haversine_distance_km(
            *map(float, waypoints[i].split(',')), 
            *map(float, waypoints[i + 1].split(','))
        )
        i += 1

    trip_patterns: List[TripPattern] = []

    # If entire route fits into bicycle distance, no public transport needed
    if i + 1 == len(waypoints) and distance * 1.2 <= max_bike_distance:
        return []
    else:
        # Determine drop-off adjustment
        distance_to_next = distance - max_bike_distance
        if len(bike_group) == 1:
            extra_distance = max_bike_distance
        else:
            extra_distance = haversine_distance_km(
                *map(float, waypoints[i - 1].split(',')), 
                *map(float, waypoints[i].split(','))
            ) - distance_to_next
        
        # Very short adjustment, skip
        if len(bike_group) == 1 and extra_distance <= 1:
            return []

        # First two algorithm cases
        if extra_distance <= 1 or distance_to_next <= 1:
            # Extra distance is less than 1km (first algorithm case)
            if extra_distance <= 1:
                print("extra distance")
                # Compute bicycle route based on the rental/own bicycle parameter
                if use_own_bike:
                    result = await group_walk_bicycle_route(
                        bike_group, 
                        time_to_depart, 
                        "bicycle", 
                        bike_average_speed, 
                        walk_speed, 
                        session, 
                        bicycle_public=True, 
                        bike_lock_time=bike_lock_time
                    )
                else:
                    result = await rental_bike_route(
                        bike_group, 
                        time_to_depart, 
                        True,
                        arrive_by, 
                        bike_lock_time, 
                        bike_average_speed, 
                        walk_speed, 
                        session, 
                        bicycle_public=True, 
                        use_semicircle=True
                    )
                
                # Process results
                for pattern in result:
                    # Invalid result
                    if not pattern.legs[-2].toPlace:
                        continue
                    
                    # Compute walk segment from bicycle station to destination
                    walk_result = await walk_bicycle_route(
                        f"{pattern.legs[-2].toPlace.latitude}, {pattern.legs[-2].toPlace.longitude}", 
                        bike_group[-1], 
                        pattern.aimedEndTime, 
                        "foot", 
                        walk_speed, 
                        session
                    )
                    
                    # Add walk result to trip pattern
                    if len(walk_result) > 0:
                        pattern.legs.extend(walk_result[0].legs)
                        pattern.aimedEndTime = walk_result[0].aimedEndTime
                        justify_time(pattern, time_to_depart, arrive_by)
                i -= 1
            # Distance to next is less than 1km (second algorithm case)
            else:
                print("distance to next")
                # Interpolation to get the bike limit point
                lat1, lon1 = map(float, waypoints[i - 1].split(','))
                lat2, lon2 = map(float, waypoints[i].split(','))
                lat, lon = interpolate_point(lat1, lon1, lat2, lon2, extra_distance * 0.8)

                bike_group.append(f"{lat}, {lon}")
                leg_index = -2

                # Compute bicycle route based on the rental/own bicycle parameter
                if use_own_bike:
                    result = await group_walk_bicycle_route(
                        bike_group, 
                        time_to_depart, 
                        "bicycle", 
                        bike_average_speed, 
                        walk_speed, 
                        session, 
                        bicycle_public=True, 
                        bike_lock_time=bike_lock_time
                    )
                else:
                    result = await rental_bike_route(
                        bike_group, 
                        time_to_depart, 
                        True, 
                        arrive_by, 
                        bike_lock_time, 
                        bike_average_speed, 
                        walk_speed, 
                        session,
                        bicycle_public=True, 
                        use_semicircle=True
                    )
                
                # Process results
                for pattern in result:
                    toPlace = pattern.legs[leg_index].toPlace

                    # Validate trip pattern
                    if not toPlace:
                        continue

                    # Compute walk segment from bicycle station to destination
                    walk_result = await walk_bicycle_route(
                        f"{toPlace.latitude}, {toPlace.longitude}", 
                        waypoints[i], 
                        pattern.aimedEndTime, 
                        "foot", 
                        walk_speed, 
                        session
                    )
                    
                    # Add walk result to trip pattern
                    if len(walk_result) > 0:
                        pattern.legs.extend(walk_result[0].legs)
                        pattern.aimedEndTime = walk_result[0].aimedEndTime
                        justify_time(pattern, time_to_depart, arrive_by)

            # No results found
            if len(result) == 0:
                return []

            # No more waypoints for routing
            if len(waypoints[i:]) < 2:
                trip_patterns.append(result[0])
            # Route using public transport
            else:
                pt_result = await process_public_route(
                    waypoints[i:], 
                    time_to_depart if arrive_by else result[0].aimedEndTime, 
                    arrive_by, 
                    max_transfers,
                    modes, 
                    walk_speed, 
                    session
                )
                
                # Process trip patterns
                for pattern in result:
                    # No public transport results found
                    if len(pt_result) == 0:
                        continue

                    # Process result
                    for pt_pattern in pt_result:
                        new_pattern = deepcopy(pattern)
                        justify_time(new_pattern, pt_pattern.legs[0].aimedStartTime, True)
                        new_pattern.legs.extend(deepcopy(pt_pattern.legs))
                        new_pattern.aimedEndTime = deepcopy(pt_pattern.aimedEndTime)
                        trip_patterns.append(new_pattern)
        # Extra distance is grater than 1km and distance to next is greater than 1km (third algorithm case)
        else:
            print("vacsie")
            result: List[TripPattern] = []
            factor = 0.9
            step = 0.05
            leg_index = -2

            # Repeat until result is found
            while len(result) == 0 and factor > 0.6:
                # Interpolation new drop-off point between the two coordinates
                lat1, lon1 = map(float, waypoints[i - 1].split(','))
                lat2, lon2 = map(float, waypoints[i].split(','))
                lat, lon = interpolate_point(lat1, lon1, lat2, lon2, extra_distance * factor)

                new_waypoint = f"{lat}, {lon}"
                leg_index = -2

                # Compute bicycle route based on the rental/own bicycle parameter
                if use_own_bike:
                    result = await group_walk_bicycle_route(
                        bike_group + [new_waypoint], 
                        time_to_depart, 
                        "bicycle", 
                        bike_average_speed, 
                        walk_speed, 
                        session, 
                        bicycle_public=True, 
                        bike_lock_time=bike_lock_time
                    )
                    
                    # Adjust time for arrive by 
                    if arrive_by and len(result) > 0:
                        justify_time(result[0], time_to_depart, True)
                else:
                    result = await rental_bike_route(
                        bike_group + [new_waypoint], 
                        time_to_depart, 
                        False, 
                        arrive_by, 
                        bike_lock_time, 
                        bike_average_speed, 
                        walk_speed, 
                        session, 
                        bicycle_public=True, 
                        use_semicircle=True
                    )
                
                # Process result
                temp_result: List[TripPattern] = []
                for pattern in result:
                    bike_distance = 0

                    # Compute total bicycle distance
                    for leg in pattern.legs:
                        if leg.mode == "bicycle":
                            bike_distance += leg.distance
                    
                    # Validate bicycle constraints
                    if bike_distance <= max_bike_distance * 1000 + 50:
                        temp_result.append(pattern)

                result = temp_result

                # Reduce interpolation factor and retry
                factor -= step

            # Compute public transport route for remaining part
            tasks: List[CoroutineType[Any, Any, List[TripPattern]]] = []
            for pattern in result:

                # Extract bicycle drop-off location
                toPlace = pattern.legs[leg_index].toPlace

                # Drop-off location does not exist
                if toPlace is None:
                    continue

                # Plan public transport from drop-off point
                tasks.append(
                    process_public_route(
                        [f"{toPlace.latitude}, {toPlace.longitude}", *waypoints[i:]],
                        time_to_depart if arrive_by else pattern.aimedEndTime, 
                        arrive_by, 
                        max_transfers, 
                        modes, 
                        walk_speed, 
                        session
                    )
                )

            results = await asyncio.gather(*tasks)

            # Combine results
            trip_patterns = combine_patterns(
                result, 
                results, 
                False, 
                partial_without_pt=True, 
                keep_without_connections=False
            )

    return trip_patterns

# End of file bicycle_public_route.py
