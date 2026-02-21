"""
file: process_public_route.py

Implements incremental public transport routing between multiple waypoints.
It partitions the input waypoints into logical groups based on geographic
distance and processes them sequentially. For the longer segments than a defined
threshold, 1km, the public transport routing is executed. For shorter segments,
a direct walking is enabled as a fallback.
"""

import asyncio
from typing import List
from gql.client import AsyncClientSession
from models.types import TripPattern
from services.otp_service import public_transport_route
from utils.geo import haversine_distance
from utils.planner_utils import combine_pt

async def process_public_route(
    waypoints: List[str],
    time_to_depart: str,
    arrive_by: bool,
    max_transfers: int,
    modes: List[str],
    walk_speed: float,
    session: AsyncClientSession
) -> List[TripPattern]:
    """
    The function incrementally processes waypoint segments and queries
    the OTP public transport router for each logical group of waypoints

    Args:
        waypoints: Ordered list of coordinates
        time_to_depart: Departure time in ISO format
        arrive_by: If ture, routing is computed in arrive by mode
        max_transfers: Maximum allowed number of public transport transfers
        modes: List of allowed transport modes
        walk_speed: Walking speed
        session: Asynchronous GraphQL client session
    
    Returns:
        List of computed TripPattern objects
    """
    print("function: process_public_route")
    i = 0
    trip_patterns = []
    num_of_waypoints = len(waypoints)

    # Arrive by mode
    if arrive_by:
        i = len(waypoints) - 1

        # Iterates over all waypoints
        while i > 0:
            group: List[str] = []
            distance = 10

            # While not all waypoints are processed or the distance to next is less than 1km
            while distance >= 1 and i > 0:
                group.insert(0, waypoints[i])
                distance = haversine_distance(*map(float, waypoints[i - 1].split(',')), *map(float, waypoints[i].split(',')))
                i -= 1

            # Add first waypoint
            if distance >= 1:
                group.insert(0, waypoints[i])
                i -= 1

            # Multiple waypoints more than 1km apart found
            if len(group) > 1:
                # Route using public transport
                tasks = [
                    public_transport_route(group, pattern["legs"][0]["aimedStartTime"], arrive_by, max_transfers, modes, session, num_of_waypoints, walk_speed)
                    for pattern in trip_patterns
                ]

                # Routing first part
                if tasks == []:
                    tasks.append(public_transport_route(group, time_to_depart, arrive_by, max_transfers, modes, session, num_of_waypoints, walk_speed))
                
                results = await asyncio.gather(*tasks)

                # Routing first part
                if trip_patterns == []:
                    trip_patterns = results[0]
                else:
                    trip_patterns = combine_pt(trip_patterns, results, arrive_by, keep_base=False) 
            
            # Segments shorter than 1km found
            if i >= 0:
                # Route using public transport with direct mode enabled
                tasks = [
                    public_transport_route([waypoints[i], group[0]], pattern["legs"][0]["aimedStartTime"], arrive_by, max_transfers, modes, session, num_of_waypoints, walk_speed, add_direct_mode=True)
                    for pattern in trip_patterns
                ]

                # Routing first part
                if tasks == []:
                    tasks.append(public_transport_route([waypoints[i], group[0]], time_to_depart, arrive_by, max_transfers, modes, session, num_of_waypoints, walk_speed, add_direct_mode=True))
                
                results = await asyncio.gather(*tasks)

                # Routing first part
                if trip_patterns == []:
                    trip_patterns = results[0]
                else:
                    trip_patterns = combine_pt(trip_patterns, results, arrive_by, keep_base=False)
    # Departure mode
    else:
        i = 0
        first_iteration = True

        # Iterates over all waypoints
        while i + 1 < len(waypoints):
            group = []
            distance = 10

            # While not all waypoints are processed or the distance to next is less than 1km
            while distance >= 1 and i + 1 < len(waypoints):
                group.append(waypoints[i])
                distance = haversine_distance(*map(float, waypoints[i].split(',')), *map(float, waypoints[i + 1].split(',')))
                i += 1

            # Add final waypoint
            if distance >= 1:
                group.append(waypoints[i])
                i += 1

            # Multiple waypoints more than 1km apart found
            if len(group) > 1:
                # Route using public transport
                tasks = [
                    public_transport_route(group, pattern["aimedEndTime"], arrive_by, max_transfers, modes, session, num_of_waypoints, walk_speed)
                    for pattern in trip_patterns
                ]

                # Routing first part
                if tasks == []:
                    tasks.append(public_transport_route(group, time_to_depart, arrive_by, max_transfers, modes, session, num_of_waypoints, walk_speed))
                
                results = await asyncio.gather(*tasks)

                # Routing first part
                if trip_patterns == [] and first_iteration:
                    trip_patterns = results[0]
                else:
                    trip_patterns = combine_pt(trip_patterns, results, arrive_by, keep_base=False)
            
            # Segments shorter than 1km found
            if i < len(waypoints):
                # Route using public transport with direct mode enabled
                tasks = [
                    public_transport_route([group[-1], waypoints[i]], pattern["aimedEndTime"], arrive_by, max_transfers, modes, session, num_of_waypoints, walk_speed, add_direct_mode=True)
                    for pattern in trip_patterns
                ]

                # Routing first part
                if tasks == []:
                    tasks.append(public_transport_route([group[-1], waypoints[i]], time_to_depart, arrive_by, max_transfers, modes, session, num_of_waypoints, walk_speed, add_direct_mode=True))
                
                results = await asyncio.gather(*tasks)

                # Routing first part
                if trip_patterns == []:
                    trip_patterns = results[0]
                else:
                    trip_patterns = combine_pt(trip_patterns, results, arrive_by, keep_base=False)

        first_iteration = False

    return trip_patterns

# End of file public_transport_route.py
