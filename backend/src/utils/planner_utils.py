"""
file: planner_utils.py

Helper functions for trip planning logic, including:
- combining base trip patterns with the new connecting_patterns,
- grouping waypoints based on transport modes,
- filtering and sorting found trip patterns based on the user preferences,
- detecting specific sequences of transport modes in waypoint groups,
- checking proximity of a position to a waypoint.
"""

from copy import deepcopy
from datetime import datetime
from utils.geo import haversine_distance_km
from models.route import RoutingMode, TripPattern, WaypointGroup
from models.route_data import LegPreferences, RouteData
from utils.legs_processing import justify_time
from typing import List, Tuple
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Bratislava")

def ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)

def combine_patterns(
    partial_patterns: List[TripPattern],
    connecting_patterns: List[List[TripPattern]],
    arrive_by: bool,
    partial_without_pt: bool = False,
    keep_without_connections: bool = True,
    patterns_validity: List[bool] | None = None,
    public_bicycle: bool = False
) -> List[TripPattern]:
    """
    Combines partial trip patterns with the following connecting patterns

    Args:
        partial_patterns: List of already constructed trip patterns
        connecting_patterns: List of lists containing new patterns corresponding to each partial pattern
        arrive_by: If true, the planning is arrival based, if false, departure based
        partial_without_pt: If true, partial patterns do not contain public transport, therefore time can be adjusted
        keep_without_connections: If true, partial patterns are kept when no new connecting patterns are available
        patterns_validity: Mask for filtering partial_patterns
        public_bicycle: Parameter indicating routing public_bicycle transport

    Returns:
        List of combined trip patterns
    """
    print("function: combine_patterns")
    trip_patterns: List[TripPattern] = []

    # Iterates over all pattern pairs
    for i, (partial_pattern, connections) in enumerate(zip(partial_patterns, connecting_patterns)):
        # Ignore invalid patterns
        if patterns_validity is not None and not patterns_validity[i]:
            continue

        # Keep only partial patterns if there are no new connecting patterns and it is allowed
        if len(connections) == 0 and keep_without_connections:
            trip_patterns.append(partial_pattern)
        else:
            # For each possible connection pattern corresponding to the current partial pattern, create a combined result
            for connection in connections:
                combined = deepcopy(partial_pattern)

                # Arrival based routing
                if arrive_by:
                    new_legs = deepcopy(connection.legs)
                    new_modes = deepcopy(connection.modes)

                    # Justify pattern times when public transport is used in first route segment
                    if partial_without_pt:
                        if public_bicycle:
                            # Shift the partial pattern in time so that its start aligns with the end of the connecting pattern
                            justify_time(combined, new_legs[-1].aimedEndTime, False)
                        else:
                            # Shift the connecting pattern in time so that its end aligns with the start of the partial pattern
                            justify_time(
                                TripPattern(
                                    aimedEndTime=datetime.min,   # Dummy value
                                    legs=new_legs
                                ),
                                partial_pattern.legs[0].aimedStartTime,
                                True
                            )
                    
                    # Attach connection legs before existing partial legs
                    new_legs.extend(deepcopy(combined.legs))
                    new_modes.extend(deepcopy(combined.modes))

                    combined.legs = new_legs
                    combined.modes = new_modes
                # Departure based routing
                else:
                    # Justify pattern times when public transport is used in first route segment
                    if partial_without_pt:
                        justify_time(combined, connection.legs[0].aimedStartTime, True)

                    # Attach new legs after partial_pattern legs
                    combined.legs.extend(connection.legs)
                    combined.aimedEndTime = connection.aimedEndTime
                    combined.modes = combined.modes + connection.modes
                trip_patterns.append(combined)
    return trip_patterns

def create_waypoint_groups(
    waypoints: List[str],
    pref: List[LegPreferences],
    multimodal: bool = True,
    mode: RoutingMode | None = None
) -> Tuple[List[WaypointGroup], bool]:
    """
    The function splits a sequence of waypoints into consecutive groups
    according to the modes used in trip segments

    Args:
        waypoints: Ordered list of waypoint identifiers
        pref: List of leg preferences corresponding to waypoint legs
        multimodal: If false, all waypoints are grouped into a single segment
        mode: The transport mode used when multimodal routing is disabled
    
    Returns:
        tuple (list of waypoint groups, boolean if the bicycle segment was found)
    """
    print("function: create_waypoint_groups")
    # Unimodal routing
    if not multimodal:
        if not mode:
            raise RuntimeError("Mode not defined unimodal route")
        return [
            WaypointGroup(
                group=waypoints,
                mode=mode
            )
        ], False

    # Multimodal routing
    groups: List[WaypointGroup] = []
    bike_segment_found = False
    i = 0

    # Iterates over waypoints
    while i < len(waypoints) - 1:
        # Get the waypoint pair and mode on trip segment
        group = [waypoints[i], waypoints[i + 1]]
        mode = pref[i].mode if i < len(pref) else None
        j = i

        # Set the bicycle segment found
        if mode == "bicycle":
            bike_segment_found = True

        # Group all consecutive segments with the same mode
        while j < len(pref) - 1 and pref[j + 1].mode == mode:
            group.append(waypoints[j + 2])
            j += 1

        groups.append(
            WaypointGroup(
                group=group,
                mode=mode
            )
        )
        i = j + 1

    return groups, bike_segment_found

def filter_sort_trip_patterns(trip_patterns: List[TripPattern], data: RouteData) -> List[TripPattern]:
    """
    Filters and sort found trip patterns based on the user preferences

    Args:
        trip_patterns: List of all found trip patterns
        data: Data object including user preferences

    Returns:
        Sorted and filtered list of the best trip patterns (max 10)
    """
    print("function: filter_sort_trip_patterns")
    new_patterns: List[TripPattern] = []

    # Get the maximal bicycle/bikesharing distance
    max_bike_distance = data.max_bike_distance if data.use_own_bike else data.max_bikesharing_distance

    # The foot segment set in user preferences in multimodal routing or foot selected for unimodal routing
    foot_in_pref = (any(lp.mode == "foot" for lp in data.leg_preferences) and data.mode == "transit,bicycle,walk") or data.mode == "foot"
    
    # Filter trip patterns based on the user preferences
    for pattern in trip_patterns:
        # Check the maximal number of transfers
        if pattern.numOfTransfers and pattern.numOfTransfers > data.max_transfers:
            continue

        # Check the maximal walk distance
        if pattern.walkDistance and pattern.walkDistance > data.max_walk_distance * 1000 + 50:
            # If the foot leg is set by user, set flag the walk distance is too long to the trip pattern 
            if foot_in_pref:
                pattern.tooLongWalkDistance = True  
            # The trip pattern will not be shown
            else:
                continue
        # Check the maximal bicycle distance and set the flag for pattern
        if pattern.bikeDistance and pattern.bikeDistance > max_bike_distance * 1000 + 50:
            pattern.tooLongBikeDistance = True

        new_patterns.append(pattern)

    # Sort trip patterns based on the user preferences, the shortest trip patterns
    if data.route_preference == "shortest":
        sorted_patterns = sorted(new_patterns, key=lambda tp: tp.totalDistance if tp.totalDistance else float("inf"))
    # Sort trip patterns based on the user preferences, the minimum number of transfers
    elif data.route_preference == "transfers":
        sorted_patterns = sorted(new_patterns, key=lambda tp: (tp.numOfTransfers is not None, tp.numOfTransfers if tp.numOfTransfers else 0))
    # Sort trip patterns based on the user preferences, the shortest trip patterns, the time preference
    else:
        # The latest possible departure
        if data.arrive_by:
            sorted_patterns = sorted(new_patterns, key=lambda tp: ensure_aware(tp.legs[0].aimedStartTime), reverse=True)
        # The soonest possible arrival
        else:
            sorted_patterns = sorted(new_patterns, key=lambda tp: ensure_aware(tp.aimedEndTime))
    
    # Return max 10 trip patterns
    return sorted_patterns[:10]

def contains_sublist(list: List[WaypointGroup], sublist: List[str]) -> bool:
    """
    Check whether a list of waypoint groups contains a given contiguous 
    subsequence of transport modes

    Args:
        list: List of waypoint groups
        sublist: List of transport modes

    Returns:
        True if the subsequence of modes is present, false otherwise
    """
    # Iterates over the list with the sliding window
    for i in range(len(list) - len(sublist) + 1):
        # Compare modes of the current window with the target sublist
        if [group.mode for group in list[i:i+len(sublist)]] == sublist:
            return True
    return False

def at_waypoint(lat: float, lon: float, waypoint: str) -> bool:
    """
    Check whether a given geographic position is close a specified waypoint

    Args:
        lat: Latitude of the given position
        lon: Longitude of the given position
        waypoint: Waypoint coordinates in format lat,lon
    
    Returns:
        True, if the position is within 50 meters of the waypoint, false otherwise
    """
    # Get waypoint coordinates
    waypoint_lat, waypoint_lon = map(float, waypoint.split(','))

    # Compute distance in meters
    distance_m = haversine_distance_km(lat, lon, waypoint_lat, waypoint_lon) * 1000

    return distance_m < 50

# End of file planner_utils.py
