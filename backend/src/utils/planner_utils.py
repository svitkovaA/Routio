"""
file: planner_utils.py

Helper functions for trip planning logic, including:
- combining base trip patterns with the new results,
- grouping waypoints based on transport modes,
- filtering and sorting found trip patterns based on the user preferences,
- detecting specific sequences of transport modes in waypoint groups,
- checking proximity of a position to a waypoint.
"""

from copy import deepcopy
from utils.geo import haversine_distance
from models.route import TripPattern, WaypointGroup
from models.route_data import LegPreferences, RouteData
from utils.legs_processing import justify_time
from typing import List, Tuple

def combine_pt(
    base_patterns: List[TripPattern],
    results: List[List[TripPattern]],
    arrive_by: bool,
    first_pt: bool=False,
    keep_base: bool = True,
    validity: List[bool] | None = None,
    combination: bool = False
) -> List[TripPattern]:
    """
    Combines base trip patterns with the new results

    Args:
        base_patterns: List of base trip patterns to be extended
        results: List of lists containing new patterns corresponding to each base pattern
        arrive_by: Indicates if the planning is arrival or departure based
        first_pt: Indicates whether the public transport is the first part of the trip
        keep_base: If true, base patterns are kept when no new results are available
        validity: List indicating validity of the individual results
        combination: Parameter indicating routing public_bicycle transport

    Returns:
        List of combined trip patterns
    """
    print("function: combine_pt")
    trip_patterns: List[TripPattern] = []

    # Iterates over pattern pairs
    for i, (base, new_patterns) in enumerate(zip(base_patterns, results)):
        # Ignore invalid patterns
        if validity is not None and not validity[i]:
            continue

        # Keep base patterns without results
        if len(new_patterns) == 0 and keep_base:
            trip_patterns.append(base)
        else:
            for np in new_patterns:
                combined = deepcopy(base)
                if arrive_by:
                    new_legs = deepcopy(np["legs"])
                    new_modes = deepcopy(np.get("modes", []))
                    # Justify pattern times when only one public transport pattern present
                    if first_pt:
                        # Shift shared bike times to public transport end time
                        if combination:
                            justify_time(combined, new_legs[-1]["aimedEndTime"], False)
                        else:
                            justify_time({"aimedEndTime": "", "legs": new_legs}, base["legs"][0]["aimedStartTime"], True)
                    
                    # Attach new legs before base legs
                    new_legs.extend(deepcopy(combined["legs"]))
                    new_modes.extend(deepcopy(combined.get("modes", [])))
                    combined["legs"] = new_legs
                    combined["modes"] = new_modes
                else:
                    # Justify pattern times when only one public transport pattern present
                    if first_pt:
                        justify_time(combined, np["legs"][0]["aimedStartTime"], True)

                    # Attach new legs after base legs
                    combined["legs"].extend(np["legs"])
                    combined["aimedEndTime"] = np["aimedEndTime"]
                    combined["modes"] = combined.get("modes", []) + np.get("modes", [])
                trip_patterns.append(combined)
    return trip_patterns

def create_waypoint_groups(
    waypoints: List[str],
    pref: List[LegPreferences],
    multimodal: bool = True,
    mode: str = ""
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
        return [{"group": waypoints, "mode": mode, "tripPatterns": []}], False

    # Multimodal routing
    groups: List[WaypointGroup] = []
    bike_segment_found = False
    i = 0

    # Iterates over waypoints
    while i < len(waypoints) - 1:
        # Get the waypoint pair and mode on trip segment
        group = [waypoints[i], waypoints[i + 1]]
        mode = pref[i].mode if i < len(pref) else ""
        j = i

        # Set the bicycle segment found
        if mode == "bicycle":
            bike_segment_found = True

        # Group all consecutive segments with the same mode
        while j < len(pref) - 1 and pref[j + 1].mode == mode:
            group.append(waypoints[j + 2])
            j += 1
        groups.append({"group": group, "mode": mode})
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
        if pattern.get("numOfTransfers", 0) > data.max_transfers:
            continue

        # Check the maximal walk distance
        if "walkDistance" in pattern and pattern["walkDistance"] > data.max_walk_distance * 1000 + 50:
            # If the foot leg is set by user, set flag the walk distance is too long to the trip pattern 
            if foot_in_pref:
                pattern["tooLongWalkDistance"] = True  
            # The trip pattern will not be shown
            else:
                continue
        # Check the maximal bicycle distance and set the flag for pattern
        if "bikeDistance" in pattern and pattern["bikeDistance"] > max_bike_distance * 1000 + 50:
            pattern["tooLongBikeDistance"] = True

        new_patterns.append(pattern)

    # Sort trip patterns based on the user preferences, the shortest trip patterns
    if data.route_preference == "shortest":
        sorted_patterns = sorted(new_patterns, key=lambda tp: tp.get("totalDistance", float("inf")))
    # Sort trip patterns based on the user preferences, the minimum number of transfers
    elif data.route_preference == "transfers":
        sorted_patterns = sorted(new_patterns, key=lambda tp: ("numOfTransfers" in tp, tp.get("numOfTransfers", 0)))
    # Sort trip patterns based on the user preferences, the shortest trip patterns, the time preference
    else:
        # The latest possible departure
        if data.arrive_by:
            sorted_patterns = sorted(new_patterns, key=lambda tp: tp["legs"][0]["aimedStartTime"], reverse=True)
        # The soonest possible arrival
        else:
            sorted_patterns = sorted(new_patterns, key=lambda tp: tp["aimedEndTime"])
    
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
        if [group["mode"] for group in list[i:i+len(sublist)]] == sublist:
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
    distance_m = haversine_distance(lat, lon, waypoint_lat, waypoint_lon) * 1000

    return distance_m < 50

# End of file planner_utils.py
