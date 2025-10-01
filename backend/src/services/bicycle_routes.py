import asyncio
from copy import deepcopy
from services.bicycle_service.rack_service import optimal_bike_rack_choice
from services.otp_service import walk_bicycle_route

async def group_walk_bicycle_route(waypoint_group, time_to_depart: str, mode: str, session, bicycle_public: bool = False, use_bike_rack: bool = True):
    print("function: group_walk_bicycle_route")
    if mode == "bicycle" and use_bike_rack:
        return await bicycle_route(waypoint_group, time_to_depart, session, bicycle_public)
    trip_patterns = []
    tasks = [
        walk_bicycle_route(waypoint_group[k], waypoint_group[k + 1], time_to_depart, mode, session)
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

async def bicycle_route(waypoint_group, time_to_depart: str, session, bicycle_public: bool):
    print("function: bicycle_route")
    sorted_racks = await optimal_bike_rack_choice(bicycle_public, *waypoint_group[-2:])
    if len(sorted_racks) == 0:
        return []

    base_trip_patterns = await group_walk_bicycle_route(waypoint_group[:-1], time_to_depart, "bicycle", session, use_bike_rack=False)
    
    # rack_indices = [0, 1] if bicycle_public and len(sorted_racks) > 1 else [0]
    rack_indices = [0]
    trip_patterns = []

    for index in rack_indices:
        rack = sorted_racks[index]

        if len(base_trip_patterns) > 0:
            trip_pattern = deepcopy(base_trip_patterns[0])

            bike_route = await walk_bicycle_route(f"{trip_pattern["legs"][-1]["toPlace"]["latitude"]}, {trip_pattern["legs"][-1]["toPlace"]["longitude"]}", f"{rack["place"]["latitude"]}, {rack["place"]["longitude"]}", time_to_depart, "bicycle", session)
            trip_pattern["legs"].extend(bike_route[0]["legs"])

        else:
            bike_route = await walk_bicycle_route(waypoint_group[0], f"{rack["place"]["latitude"]}, {rack["place"]["longitude"]}", time_to_depart, "bicycle", session)
            trip_pattern = bike_route[0]

        trip_pattern["legs"].append({
            "mode": "wait",
            "color": "black",
            "distance": 0,
            "duration": 120,
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
        })
        if not bicycle_public:
            walk_route = await walk_bicycle_route(f"{rack["place"]["latitude"]}, {rack["place"]["longitude"]}", waypoint_group[-1], time_to_depart, "foot", session)
            trip_pattern["legs"].extend(walk_route[0]["legs"])
        trip_patterns.append(trip_pattern)
    return trip_patterns
