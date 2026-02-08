import asyncio
from copy import deepcopy
from typing import List
from models.types import Leg, TripPattern
from services.bicycle_service.rack_service import optimal_bike_rack_choice
from services.otp_service import walk_bicycle_route
from gql.client import AsyncClientSession

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
    print("function: group_walk_bicycle_route")
    if mode == "bicycle" and use_bike_rack:
        return await bicycle_route(waypoint_group, time_to_depart, bike_speed, walk_speed, session, bicycle_public, bike_lock_time * 60)
    trip_patterns = []
    tasks = [
        walk_bicycle_route(waypoint_group[k], waypoint_group[k + 1], time_to_depart, mode, walk_speed if mode == "foot" else bike_speed, session)
        for k in range(len(waypoint_group) - 1)
    ]
    results_list = await asyncio.gather(*tasks)

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
    print("function: bicycle_route")
    sorted_racks = await optimal_bike_rack_choice(bicycle_public, *waypoint_group[-2:], max_distance=1000)
    if len(sorted_racks) == 0:
        return []

    base_trip_patterns = await group_walk_bicycle_route(waypoint_group[:-1], time_to_depart, "bicycle", bike_speed, walk_speed, session, use_bike_rack=False)
    
    # rack_indices = [0, 1] if bicycle_public and len(sorted_racks) > 1 else [0]
    rack_indices = [0]
    trip_patterns: List[TripPattern] = []

    for index in rack_indices:
        rack = sorted_racks[index]

        if len(base_trip_patterns) > 0:
            trip_pattern = deepcopy(base_trip_patterns[0])

            if "toPlace" not in trip_pattern["legs"][-1]:
                continue
            bike_route = await walk_bicycle_route(f"{trip_pattern["legs"][-1]["toPlace"]["latitude"]}, {trip_pattern["legs"][-1]["toPlace"]["longitude"]}", f"{rack["place"]["latitude"]}, {rack["place"]["longitude"]}", time_to_depart, "bicycle", bike_speed, session)
            trip_pattern["legs"].extend(bike_route[0]["legs"])

        else:
            bike_route = await walk_bicycle_route(waypoint_group[0], f"{rack["place"]["latitude"]}, {rack["place"]["longitude"]}", time_to_depart, "bicycle", bike_speed, session)
            trip_pattern = bike_route[0]

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

        trip_pattern["legs"].append(wait_leg)
        if not bicycle_public:
            walk_route = await walk_bicycle_route(f"{rack["place"]["latitude"]}, {rack["place"]["longitude"]}", waypoint_group[-1], time_to_depart, "foot", walk_speed, session)
            trip_pattern["legs"].extend(walk_route[0]["legs"])
        trip_patterns.append(trip_pattern)
    return trip_patterns

# End of file bicycle_routes.py
