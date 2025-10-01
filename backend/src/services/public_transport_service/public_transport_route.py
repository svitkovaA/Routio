import asyncio
from typing import List
from services.otp_service import public_transport_route
from utils.geo import haversine_distance
from utils.planner_utils import combine_pt

async def process_public_route(waypoints: List[str], time_to_depart: str, arrive_by: bool, max_transfers: int, modes: List[str], session):
    print("function: process_public_route")
    i = 0
    trip_patterns = []
    num_of_waypoints = len(waypoints)
    if arrive_by:
        i = len(waypoints) - 1
        while i > 0:
            group = []
            distance = 10
            while distance >= 1 and i > 0:
                group.insert(0, waypoints[i])
                distance = haversine_distance(*map(float, waypoints[i - 1].split(',')), *map(float, waypoints[i].split(',')))
                i -= 1
            if distance >= 1:
                group.insert(0, waypoints[i])
                i -= 1
            if len(group) > 1:
                tasks = [
                    public_transport_route(group, pattern["legs"][0]["aimedStartTime"], arrive_by, max_transfers, modes, session, num_of_waypoints)
                    for pattern in trip_patterns
                ]
                if tasks == []:
                    tasks.append(public_transport_route(group, time_to_depart, arrive_by, max_transfers, modes, session, num_of_waypoints))
                print(time_to_depart)
                results = await asyncio.gather(*tasks)
                if trip_patterns == []:
                    trip_patterns = results[0]
                else:
                    trip_patterns = combine_pt(trip_patterns, results, arrive_by, keep_base=False) 
            if i >= 0:
                tasks = [
                    public_transport_route([waypoints[i], group[0]], pattern["legs"][0]["aimedStartTime"], arrive_by, max_transfers, modes, session, num_of_waypoints, add_direct_mode=True)
                    for pattern in trip_patterns
                ]
                if tasks == []:
                    tasks.append(public_transport_route([waypoints[i], group[0]], time_to_depart, arrive_by, max_transfers, modes, session, num_of_waypoints, add_direct_mode=True))
                results = await asyncio.gather(*tasks)
                if trip_patterns == []:
                    trip_patterns = results[0]
                else:
                    trip_patterns = combine_pt(trip_patterns, results, arrive_by, keep_base=False)
    else:
        i = 0
        first_iteration = True
        while i + 1 < len(waypoints):
            group = []
            distance = 10
            while distance >= 1 and i + 1 < len(waypoints):
                group.append(waypoints[i])
                distance = haversine_distance(*map(float, waypoints[i].split(',')), *map(float, waypoints[i + 1].split(',')))
                i += 1
            if distance >= 1:
                group.append(waypoints[i])
                i += 1
            if len(group) > 1:
                tasks = [
                    public_transport_route(group, pattern["aimedEndTime"], arrive_by, max_transfers, modes, session, num_of_waypoints)
                    for pattern in trip_patterns
                ]
                if tasks == []:
                    tasks.append(public_transport_route(group, time_to_depart, arrive_by, max_transfers, modes, session, num_of_waypoints))
                results = await asyncio.gather(*tasks)
                if trip_patterns == [] and first_iteration:
                    trip_patterns = results[0]
                else:
                    trip_patterns = combine_pt(trip_patterns, results, arrive_by, keep_base=False)
            if i < len(waypoints):
                tasks = [
                    public_transport_route([group[-1], waypoints[i]], pattern["aimedEndTime"], arrive_by, max_transfers, modes, session, num_of_waypoints, add_direct_mode=True)
                    for pattern in trip_patterns
                ]
                if tasks == []:
                    tasks.append(public_transport_route([group[-1], waypoints[i]], time_to_depart, arrive_by, max_transfers, modes, session, num_of_waypoints, add_direct_mode=True))
                results = await asyncio.gather(*tasks)
                if trip_patterns == []:
                    trip_patterns = results[0]
                else:
                    trip_patterns = combine_pt(trip_patterns, results, arrive_by, keep_base=False)
        first_iteration = False
    return trip_patterns
