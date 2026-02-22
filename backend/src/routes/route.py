"""
file: route.py

Route API endpoints, including:
- recalculating route after changing bicycle station,
- processing user inputs and calculating optimal trip patterns.
"""

import time as t
from copy import deepcopy
from datetime import datetime
from typing import List, Literal
from fastapi import APIRouter, HTTPException
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from config.external import OTP_URL
from models.route import BikeStationInfo, Leg, Mode, PointOnLink, Results, RoutingMode, TripPattern
from models.route_data import LegPreferences, RouteData
from models.bike_station_data import BikeStationData
from services.route import route
from services.otp_service import walk_bicycle_route
from utils.planner_utils import at_waypoint, create_waypoint_groups, filter_sort_trip_patterns
from utils.legs_processing import justify_time, process_legs

router = APIRouter()

@router.post("/changeBikeStation")
async def change_bike_station(data: BikeStationData):
    """
    Recalculates a route after changing a bicycle or bikesharing station
    
    Args:
        data: Data with the original route, selected bike station,
            routing preferences, and context required for recomputation
    
    Returns:
        A new trip pattern representing the updated route with the selected
        bike station applied
    """
    print("endpoint: change_bike_station")
    route_data = data.route_data
    legs = data.original_legs
    new_legs: List[Leg] = []
    new_pattern = TripPattern(
        legs=[],
        aimedEndTime=datetime.min
    )

    # Extract only the part of the route affected by the bike station change
    # (prefix for arrive based routing, suffix for departure based routing)
    compressed_legs = (
        data.legs[:data.leg_index + 2] 
        if route_data.arrive_by 
        else data.legs[data.leg_index - 1:]
    )
    
    # Reference time used to rerouting
    time_to_depart = (
        compressed_legs[-1].aimedEndTime
        if route_data.arrive_by 
        else compressed_legs[0].aimedStartTime
    )
    
    # Time needed to lock/unlock bike
    lock_time = (
        route_data.bike_lock_time * 60 
        if route_data.use_own_bike 
        else route_data.bikesharing_lock_time * 60
    )

    # Bike/bikesharing speed
    speed = (
        route_data.bike_average_speed 
        if route_data.use_own_bike 
        else route_data.bikesharing_average_speed
    )

    fromPlace = data.bike_stations[data.new_index].place
    
    # Create connection to OpenTripPlanner
    transport = AIOHTTPTransport(url=OTP_URL)
    async with Client(transport=transport) as session:
        # Arrival based routing
        if route_data.arrive_by:

            # The origin bike station is changed
            if data.origin_bike_station:
                i = 0
                compressed_index = 0
                waypoint_count = 1
                mode: Mode | Literal[""] = ""

                # Find the first leg affected by the bike station change
                while i < len(legs) - 1 and compressed_index < len(compressed_legs) - 1:
                    if legs[i].mode == compressed_legs[compressed_index].mode:
                        compressed_index += 1
                    
                    # Count consecutive foot/bicycle segments
                    if mode == legs[i].mode and mode in ["bicycle", "foot"]:
                        waypoint_count += 1

                    mode = legs[i].mode
                    i += 1

                # Preserve unaffected suffix of the original route
                base_legs = deepcopy(legs[i+1:])
                i = len(legs) - len(base_legs) - 1

                # Compute new bicycle route from selected bike station
                toPlace = legs[i].toPlace

                if not toPlace:
                    raise HTTPException(
                        status_code = 400,
                        detail = "ToPlace missing in data"
                    )

                bike_pattern = await walk_bicycle_route(
                    f"{fromPlace.latitude}, {fromPlace.longitude}", 
                    f"{toPlace.latitude}, {toPlace.longitude}", 
                    time_to_depart, 
                    "bicycle", 
                    speed, 
                    session
                )
                
                # Append bicycle leg
                new_legs.extend(bike_pattern[0].legs)

                # Insert bike locking wait leg
                new_legs.insert(0, Leg(
                    mode="wait",
                    color="black",
                    distance=0,
                    duration=lock_time,
                    aimedEndTime=datetime.min,
                    aimedStartTime=datetime.min,
                    pointsOnLink=PointOnLink(
                        points=[]
                    ),
                    bikeStationInfo=BikeStationInfo(
                        rack=False,
                        latitude=fromPlace.latitude,
                        longitude=fromPlace.longitude,
                        origin=True,
                        selectedBikeStationIndex=data.new_index,
                        bikeStations=data.bike_stations
                    )
                ))

                # Reconnect modified route to original waypoints
                leg_index = i - 2
                waypoint_group = route_data.waypoints[:waypoint_count]

                # Check if the last waypoint is already reached
                waypoint_found = True
                place = legs[leg_index].fromPlace

                if len(waypoint_group) > 0 and place:
                    waypoint_found = at_waypoint(
                        place.latitude, 
                        place.longitude, 
                        waypoint_group[-1]
                    )
                
                routing_modes = data.modes[:waypoint_count-1]

                # Add walking connection if waypoint not reached
                if waypoint_found and place:
                    walk_pattern = await walk_bicycle_route(
                        f"{fromPlace.latitude} ,{fromPlace.longitude}", 
                        f"{place.latitude}, {place.longitude}", 
                        time_to_depart, 
                        "foot", 
                        route_data.walk_average_speed, 
                        session
                    )
                    new_legs[:0] = walk_pattern[0].legs
                else:
                    waypoint_group.append(f"{fromPlace.latitude} ,{fromPlace.longitude}")
                    routing_modes.append("walk_transit")
                
                # Remove walk_transit_bicycle from routing modes
                routing_modes: List[RoutingMode] = [
                    mode if mode != "walk_transit_bicycle" else "walk_transit" 
                    for mode in routing_modes
                ]
                
                # Justify timing backwards
                justify_time(
                    TripPattern(
                        legs=new_legs,
                        aimedEndTime=datetime.min
                    ),
                    time_to_depart,
                    True
                )
                
                # Reroute selected part of the trip
                waypoint_groups, _ = create_waypoint_groups(
                    waypoint_group, 
                    [
                        LegPreferences(mode=mode, wait=0) 
                        for mode in routing_modes
                    ]
                )
                route_pattern = await route(
                    waypoint_groups,
                    new_legs[0].aimedStartTime, 
                    session, 
                    True, 
                    route_data, 
                    True
                )
                
                # Merge new route with the original part
                new_pattern.modes = data.modes
                if len(route_pattern) > 0:
                    new_legs[:0] = route_pattern[0].legs
                    new_pattern.modes[:0] = route_pattern[0].modes
                new_pattern.legs = new_legs + base_legs
                new_pattern.aimedEndTime = new_pattern.legs[-1].aimedEndTime
                
                # Legs post-processing
                process_legs(new_pattern)

            # The destination bike station is changed
            else:
                i = 0
                compressed_index = 0
                waypoint_count = 1
                mode = ""

                # Find the first leg affected by the bike station change
                while i < len(legs) - 1 and compressed_index < len(compressed_legs) - 1:
                    if legs[i].mode == compressed_legs[compressed_index].mode:
                        compressed_index += 1

                    # Count consecutive foot/bicycle segments
                    if mode == legs[i].mode and mode in ["bicycle", "foot"]:
                        waypoint_count += 1
                    mode = legs[i].mode
                    i += 1
                
                # Preserve unaffected suffix of the original route
                base_legs = deepcopy(legs[i+1:])
                i = len(legs) - len(base_legs) - 1

                toPlace = legs[i].toPlace

                if not toPlace:
                    raise HTTPException(
                        status_code = 400,
                        detail = "ToPlace missing in data"
                    )

                # Compute new foot route from selected bike station
                walk_pattern = await walk_bicycle_route(
                    f"{fromPlace.latitude} ,{fromPlace.longitude}", 
                    f"{toPlace.latitude}, {toPlace.longitude}", 
                    time_to_depart, 
                    "foot", 
                    route_data.walk_average_speed, 
                    session
                )
                
                # Append foot leg
                new_legs.extend(walk_pattern[0].legs)

                # Insert bike locking wait leg
                new_legs.insert(0, Leg(
                    mode="wait",
                    color="black",
                    distance=0,
                    duration=lock_time,
                    aimedEndTime=datetime.min,
                    aimedStartTime=datetime.min,
                    pointsOnLink=PointOnLink(
                        points=[]
                    ),
                    bikeStationInfo=BikeStationInfo(
                        rack=False,
                        latitude=fromPlace.latitude,
                        longitude=fromPlace.longitude,
                        origin=False,
                        selectedBikeStationIndex=data.new_index,
                        bikeStations=data.bike_stations
                    )
                ))

                # Reconnect modified route to original waypoints
                leg_index = i - 2

                place = legs[leg_index].fromPlace

                if not place:
                    raise HTTPException(
                        status_code = 400,
                        detail = "ToPlace missing in data"
                    )                

                if new_legs[0].bikeStationInfo:
                    # Route bicycle segment previous waypoint to new destination station
                    bike_pattern = await walk_bicycle_route(
                        f"{place.latitude}, {place.longitude}", 
                        f"{new_legs[0].bikeStationInfo.latitude}, {new_legs[0].bikeStationInfo.longitude}", 
                        time_to_depart, 
                        "bicycle", 
                        speed, 
                        session
                    )
                    
                    # Append bicycle legs before original legs
                    new_legs[:0] = bike_pattern[0].legs
                    
                    # Skip the bicycle leg
                    leg_index -= 1

                    # Iterates over all bicycle legs
                    while leg_index > 0 and legs[leg_index].mode != "foot":
                        # Adjusts waypoint count
                        if legs[leg_index].mode == "bicycle":
                            waypoint_count -= 1
                        new_legs.insert(0, deepcopy(legs[leg_index]))
                        leg_index -= 1

                    found_waypoint = True
                    waypoint_group = route_data.waypoints[:waypoint_count]

                    place = legs[leg_index].fromPlace

                    if not place:
                        raise HTTPException(
                            status_code = 400,
                            detail = "ToPlace missing in data"
                        )

                    # Determine if waypoint was reached
                    if leg_index > 0:
                        found_waypoint = at_waypoint(place.latitude, place.longitude, waypoint_group[-1])
                    
                    # Append leg if it leads to waypoint
                    if found_waypoint:
                        new_legs.insert(0, deepcopy(legs[leg_index]))
                    
                    # Adjust times in legs to eliminate gaps
                    justify_time(
                        TripPattern(
                            legs=new_legs,
                            aimedEndTime=datetime.min
                        ),
                        time_to_depart, 
                        True
                    )
                    
                    # Get routing modes for part of trip to recalculate
                    routing_modes = data.modes[:waypoint_count-1]

                    # Add artificial waypoint when public_bicycle was used
                    if not found_waypoint:
                        waypoint_group.append(f"{place.latitude}, {place.longitude}")
                        routing_modes.append("walk_transit")
                    
                    # Replace walk_transit_bicycle for walk_transit in modes
                    routing_modes = [mode if mode != "walk_transit_bicycle" else "walk_transit" for mode in routing_modes]
                    
                    # Create new waypoint groups and calculated necessary route
                    waypoint_groups, _ = create_waypoint_groups(
                        waypoint_group, 
                        [
                            LegPreferences(mode=mode, wait=0) 
                            for mode in routing_modes
                        ]
                    )
                    route_pattern = await route(
                        waypoint_groups, 
                        new_legs[0].aimedStartTime, 
                        session, 
                        True, 
                        route_data, 
                        True
                    )
                    
                    # Adjust pattern modes
                    new_pattern.modes = data.modes
                    if len(route_pattern) > 0:
                        new_legs[:0] = route_pattern[0].legs
                        new_pattern.modes[:0] = route_pattern[0].modes
                    
                    # Adjust end time
                    new_pattern.aimedEndTime = base_legs[-1].aimedEndTime if len(base_legs) > 0 else new_legs[-1].aimedEndTime
                    
                    # Combine legs
                    new_pattern.legs = new_legs + base_legs
                    
                    # Leg processing
                    process_legs(new_pattern)

        # Departure based routing
        else:
            # The origin bike station is changed
            if data.origin_bike_station:
                i = len(legs) - 1
                compressed_index = len(compressed_legs) - 1
                waypoint_count = 1
                mode: Mode | Literal[""] = ""

                # Find the first leg affected by the bike station change
                while i >= 0 and compressed_index >= 0:
                    if legs[i].mode == compressed_legs[compressed_index].mode:
                        compressed_index -= 1
                    
                    # Count consecutive foot/bicycle segments
                    if mode == legs[i].mode and mode in ["bicycle", "foot"]:
                        waypoint_count += 1

                    mode = legs[i].mode
                    i -= 1

                # Preserve unaffected prefix of the original route
                base_legs = deepcopy(legs[:i+1])
                i = len(base_legs)

                place = legs[i].fromPlace

                if not place:
                    raise HTTPException(
                        status_code = 400,
                        detail = "ToPlace missing in data"
                    ) 

                # Compute new walk route to the new selected bike station
                walk_pattern = await walk_bicycle_route(
                    f"{place.latitude}, {place.longitude}", 
                    f"{fromPlace.latitude} ,{fromPlace.longitude}",
                    time_to_depart, 
                    "foot", 
                    route_data.walk_average_speed, 
                    session
                )
                
                # Append walk leg
                new_legs.extend(walk_pattern[0].legs)

                # Insert bike locking wait leg
                new_legs.append(Leg(
                    mode="wait",
                    color="black",
                    distance=0,
                    duration=lock_time,
                    aimedEndTime=datetime.min,
                    aimedStartTime=datetime.min,
                    pointsOnLink=PointOnLink(
                        points=[]
                    ),
                    bikeStationInfo=BikeStationInfo(
                        rack=False,
                        latitude=fromPlace.latitude,
                        longitude=fromPlace.longitude,
                        origin=True,
                        selectedBikeStationIndex=data.new_index,
                        bikeStations=data.bike_stations
                    )
                ))

                # Reconnect modified route to original waypoints
                leg_index = i + 2
                if new_legs[-1].bikeStationInfo:
                    place = legs[leg_index].toPlace

                    if not place:
                        raise HTTPException(
                            status_code = 400,
                            detail = "ToPlace missing in data"
                        ) 
                    # Compute route from new origin station to next point
                    bike_pattern = await walk_bicycle_route(
                        f"{new_legs[-1].bikeStationInfo.latitude}, {new_legs[-1].bikeStationInfo.longitude}", 
                        f"{place.latitude}, {place.longitude}", 
                        time_to_depart, 
                        "bicycle", 
                        speed, 
                        session
                    )
                    
                    # Add new legs
                    new_legs.extend(bike_pattern[0].legs)
                    leg_index += 1

                    # Add bicycle remaining legs
                    while leg_index < len(legs) and legs[leg_index].mode != "foot":
                        if legs[leg_index].mode == "bicycle":
                            waypoint_count -= 1
                        new_legs.append(deepcopy(legs[leg_index]))
                        leg_index += 1
                    
                    # Determine if waypoint was reached
                    found_waypoint = True
                    if leg_index < len(legs):
                        place = legs[leg_index].toPlace

                        if not place:
                            raise HTTPException(
                                status_code = 400,
                                detail = "ToPlace missing in data"
                            )
                        
                        found_waypoint = at_waypoint(
                            place.latitude, 
                            place.longitude, 
                            data.route_data.waypoints[waypoint_count-1]
                        )
                    if found_waypoint:
                        new_legs.append(deepcopy(legs[leg_index]))

                    # Adjust times in legs to eliminate gaps
                    justify_time(
                        TripPattern(
                            legs=new_legs,
                            aimedEndTime=datetime.min
                        ),
                        time_to_depart, 
                        False
                    )
                    
                    # Get waypoint for which routing is required
                    waypoint_group = route_data.waypoints[-waypoint_count:]

                    # Get routing modes for part of trip to recalculate
                    routing_modes = data.modes[-waypoint_count+1:] if waypoint_count > 1 else []

                    place = legs[leg_index].fromPlace

                    if not place:
                        raise HTTPException(
                            status_code = 400,
                            detail = "ToPlace missing in data"
                        ) 
                    
                    # Insert artificial waypoint when bicycle_public was used
                    if not found_waypoint:
                        waypoint_group.insert(0, f"{place.latitude}, {place.longitude}")
                        routing_modes.insert(0, "walk_transit")
                    
                    # Remove bicycle_walk_transit from modes
                    routing_modes = [mode if mode != "bicycle_walk_transit" else "walk_transit" for mode in routing_modes]
                    
                    # Create new waypoint groups and calculated necessary route
                    waypoint_groups, _ = create_waypoint_groups(
                        waypoint_group, 
                        [
                            LegPreferences(mode=mode, wait=0) 
                            for mode in routing_modes
                        ]
                    )
                    route_pattern = await route(waypoint_groups, new_legs[-1].aimedEndTime, session, True, route_data, True)
                    
                    # Save modes
                    new_pattern.modes = data.modes

                    # Update legs
                    if len(route_pattern) > 0:
                        new_legs.extend(route_pattern[0].legs)
                        new_pattern.aimedEndTime = route_pattern[0].aimedEndTime
                    new_pattern.legs = base_legs + new_legs

                    # Leg processing
                    process_legs(new_pattern)

            # The destination bike station is changed
            else:
                i = len(legs) - 1
                compressed_index = len(compressed_legs) - 1
                waypoint_count = 1
                mode: Mode | Literal[""] = ""

                # Find the first leg affected by the bike station change
                while i >= 0 and compressed_index >= 0:
                    if legs[i].mode == compressed_legs[compressed_index].mode:
                        compressed_index -= 1

                    # Count consecutive foot/bicycle segments
                    if mode == legs[i].mode and mode in ["bicycle", "foot"]:
                        waypoint_count += 1
                    mode = legs[i].mode
                    i -= 1
                # Get affected waypoints
                waypoint_group = route_data.waypoints[-waypoint_count:]

                # Get base unaffected legs
                base_legs = deepcopy(legs[:i+1])
                i = len(base_legs)

                place = legs[i].fromPlace

                if not place:
                    raise HTTPException(
                        status_code = 400,
                        detail = "ToPlace missing in data"
                    ) 

                # Compute new bicycle route from selected bike station
                bike_pattern = await walk_bicycle_route(
                    f"{place.latitude}, {place.longitude}", 
                    f"{fromPlace.latitude} ,{fromPlace.longitude}", 
                    time_to_depart,
                    "bicycle",
                    speed,
                    session
                )
                
                # Append bicycle leg
                new_legs.extend(bike_pattern[0].legs)

                # Insert bike locking wait leg
                new_legs.append(Leg(
                    mode="wait",
                    color="black",
                    distance=0,
                    duration=lock_time,
                    aimedEndTime=datetime.min,
                    aimedStartTime=datetime.min,
                    pointsOnLink=PointOnLink(
                        points=[]
                    ),
                    bikeStationInfo=BikeStationInfo(
                        rack=False,
                        latitude=fromPlace.latitude,
                        longitude=fromPlace.longitude,
                        origin=False,
                        selectedBikeStationIndex=data.new_index,
                        bikeStations=data.bike_stations
                    )
                ))

                # Reconnect modified route to original waypoints
                leg_index = i + 2
                waypoint_found = True

                place = legs[leg_index].toPlace

                if not place:
                    raise HTTPException(
                        status_code = 400,
                        detail = "ToPlace missing in data"
                    ) 

                # Determine if waypoint was reached
                if len(waypoint_group) > 0:
                    waypoint_found = at_waypoint(
                        place.latitude, 
                        place.longitude,
                        waypoint_group[0]
                    )
                
                # Get routing modes
                routing_modes = data.modes[-waypoint_count+1:] if waypoint_count > 1 else []

                if new_legs[-1].bikeStationInfo:
                    # Compute foot route new bike station to next waypoint
                    if waypoint_found:
                        walk_pattern = await walk_bicycle_route(
                            f"{new_legs[-1].bikeStationInfo.latitude}, {new_legs[-1].bikeStationInfo.longitude}", 
                            f"{place.latitude}, {place.longitude}", 
                            time_to_depart, 
                            "foot", 
                            route_data.walk_average_speed, 
                            session
                        )
                        new_legs.extend(walk_pattern[0].legs)
                    # Add artificial waypoint when bicycle public used
                    else:
                        waypoint_group.insert(0, f"{new_legs[-1].bikeStationInfo.latitude}, {new_legs[-1].bikeStationInfo.longitude}")
                        routing_modes.insert(0, "walk_transit")

                # Remove bicycle_walk_transit from modes
                routing_modes = [mode if mode != "bicycle_walk_transit" else "walk_transit" for mode in routing_modes]
                
                # Adjust times in legs to eliminate gaps
                justify_time(
                    TripPattern(
                        legs=new_legs,
                        aimedEndTime=datetime.min
                    ),
                    time_to_depart, 
                    False
                )
                
                # Create new waypoint groups and calculated necessary route
                waypoint_groups, _ = create_waypoint_groups(
                    waypoint_group, 
                    [
                        LegPreferences(mode=mode, wait=0) 
                        for mode in routing_modes
                    ]
                )
                route_pattern = await route(
                    waypoint_groups, 
                    new_legs[-1].aimedEndTime, 
                    session, 
                    True, 
                    route_data, 
                    True
                )
                
                # Combine legs
                new_pattern.legs = base_legs + new_legs
                
                # Save modes
                new_pattern.modes = data.modes

                # Update legs
                if len(route_pattern) > 0:
                    new_pattern.legs.extend(route_pattern[0].legs)
                    new_pattern.aimedEndTime = route_pattern[0].aimedEndTime
                else:
                    new_pattern.aimedEndTime = new_legs[-1].aimedEndTime

                # Leg processing
                process_legs(new_pattern)

    return new_pattern

@router.post("/route")
async def get_route(data: RouteData):
    """
    The endpoint process user input data and found the optimal trip patterns
    according to user preferences

    Args:
        data: The input routing data, including waypoints, date and time,
        transport preferences, and user constraints
    
    Returns:
        Routing results containing computed trip patterns
    """
    print("endpoint: get_route")

    # Start measuring request processing time
    start = t.perf_counter()

    # Initialize response structure
    results = Results(
        tripPatterns=[],
        active=True
    )

    # Combine selected date and time into ISO-formatted datetime
    time_to_depart = datetime.combine(data.date, data.time)

    # Determine whether multimodal routing is enabled
    multimodal = data.mode == "transit,bicycle,walk"
    
    # Split waypoints into groups based on transport mode preferences
    waypoint_groups, bike_segment_found = create_waypoint_groups(data.waypoints, data.leg_preferences, multimodal, data.mode)
    
    # Query OpenTripPlanner
    transport = AIOHTTPTransport(url=OTP_URL)
    async with Client(transport=transport, execute_timeout=20) as session:
        results.tripPatterns = await route(
            waypoint_groups, 
            time_to_depart, 
            session, multimodal, 
            data, 
            bike_segment_found, 
            True
        )
    
    # Post-processing of the returned trip patterns
    for pattern in results.tripPatterns:
        process_legs(pattern)

    # Filter and sort trip patterns based on the user preferences
    results.tripPatterns = filter_sort_trip_patterns(results.tripPatterns, data)
    
    # Log request processing duration
    end = t.perf_counter()
    print(f"Duration: {end - start:.4f} sec")

    return results

# End of file route.py
