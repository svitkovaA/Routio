"""
file: bicycle_routes.py

Implements walking and bicycle routing logic for grouped waypoint segments.
"""

import asyncio
from copy import deepcopy
from typing import List
from gql.client import AsyncClientSession
from models.types import Leg, TripPattern
from services.bicycle_service.rack_service import optimal_bike_rack_choice
from services.otp_service import walk_bicycle_route

async def group_walk_bicycle_route(
    waypoint_group: List[str], 
    time_to_depart: str, 
    mode: str, 
    bike_speed: float,
    walk_speed: float,
    session: AsyncClientSession, 
    bicycle_public: bool = False, 
    use_bike_rack: bool = True, 
    bike_lock_time: int = 2
) -> List[TripPattern]:
    """
    Builds trip patterns for a group of waypoints using either walking or bicycle routing

    Args:
        waypoint_group: Ordered list of coordinates
        time_to_depart: Departure time in ISO format
        mode: Transport mode (foot or bicycle)
        bike_speed: Cycling speed
        walk_speed: Walking speed
        session: Asynchronous GraphQL client session
        bicycle_public: If true, bicycle_public is used for routing
        use_bike_rack: If True and mode is bicycle rack is used
        bike_lock_time: Time in minutes required for locking bicycle

    Returns:
        List of TripPattern objects representing computed routes across the waypoint group
    """
    print("function: group_walk_bicycle_route")

    # Delegate to bicycle function
    if mode == "bicycle" and use_bike_rack:
        return await bicycle_route(waypoint_group, time_to_depart, bike_speed, walk_speed, session, bicycle_public, bike_lock_time * 60)

    trip_patterns = []

    # Routing using bicycle/foot
    tasks = [
        walk_bicycle_route(waypoint_group[k], waypoint_group[k + 1], time_to_depart, mode, walk_speed if mode == "foot" else bike_speed, session)
        for k in range(len(waypoint_group) - 1)
    ]

    results_list = await asyncio.gather(*tasks)

    # Combine results
    for res in results_list:
        if trip_patterns == []:
            trip_patterns = res
        else:
            for pattern in trip_patterns:
                pattern["legs"].extend(res[0]["legs"])

    return trip_patterns

async def bicycle_route(
    waypoint_group: List[str], 
    time_to_depart: str,
    bike_speed: float,
    walk_speed: float,
    session: AsyncClientSession, 
    bicycle_public: bool, 
    bike_lock_time: int
) -> List[TripPattern]:
    """
    Computes bicycle route between given waypoints

    Args:
        waypoint_group: Ordered list of coordinates
        time_to_depart: Departure time in ISO format
        bike_speed: Cycling speed
        walk_speed: Walking speed
        session: Asynchronous GraphQL client session
        bicycle_public: If true, bicycle_public is used for routing
        bike_lock_time: Time in seconds required to lock the bicycle

    Returns:
        List of TripPattern objects representing bicycle routes
    """
    print("function: bicycle_route")

    # Find optimal bicycle rack
    sorted_racks = await optimal_bike_rack_choice(bicycle_public, *waypoint_group[-2:], max_distance=1000)

    # No bicycle rack found
    if len(sorted_racks) == 0:
        return []

    # Compute bicycle route excluding final waypoint
    base_trip_patterns = await group_walk_bicycle_route(waypoint_group[:-1], time_to_depart, "bicycle", bike_speed, walk_speed, session, use_bike_rack=False)
        
    # Only best rack is used
    rack = sorted_racks[0]

    # Routing between more than 2 waypoints
    if len(base_trip_patterns) > 0:
        trip_pattern = deepcopy(base_trip_patterns[0])

        if "toPlace" not in trip_pattern["legs"][-1]:
            return []
        
        # Extend cycling route from last segment endpoint to rack
        bike_route = await walk_bicycle_route(f"{trip_pattern["legs"][-1]["toPlace"]["latitude"]}, {trip_pattern["legs"][-1]["toPlace"]["longitude"]}", f"{rack["place"]["latitude"]}, {rack["place"]["longitude"]}", time_to_depart, "bicycle", bike_speed, session)
        trip_pattern["legs"].extend(bike_route[0]["legs"])
    
    # Routing between 2 waypoints
    else:
        bike_route = await walk_bicycle_route(waypoint_group[0], f"{rack["place"]["latitude"]}, {rack["place"]["longitude"]}", time_to_depart, "bicycle", bike_speed, session)
        trip_pattern = bike_route[0]

    # Prepare lock time leg
    wait_leg: Leg = {
        "mode": "wait",
        "color": "black",
        "distance": 0,
        "duration": bike_lock_time,
        "aimedStartTime": "",
        "aimedEndTime": "",
        "pointsOnLink": {
            "points": []
        },
        "bikeStationInfo": {
            "rack": True,
            "latitude": rack["place"]["latitude"],
            "longitude": rack["place"]["longitude"],
            "origin": False,
            "selectedBikeStationIndex": 0,
            "bikeStations": sorted_racks
        }
    }

    # Insert lock time leg
    trip_pattern["legs"].append(wait_leg)

    # Optional walking segment to destination
    if not bicycle_public:
        walk_route = await walk_bicycle_route(f"{rack["place"]["latitude"]}, {rack["place"]["longitude"]}", waypoint_group[-1], time_to_depart, "foot", walk_speed, session)
        trip_pattern["legs"].extend(walk_route[0]["legs"])

    return [trip_pattern]

# End of file bicycle_routes.py
