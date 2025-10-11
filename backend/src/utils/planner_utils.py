from copy import deepcopy
from models.types import TripPattern, WaypointGroup
from models.route_data import LegPreferences, RouteData
from utils.legs_processing import justify_time
from typing import List

def combine_pt(base_patterns: List[TripPattern], results: List[List[TripPattern]], arrive_by: bool, first_pt: bool=False, keep_base: bool = True, validity: List[bool] | None = None, combination: bool = False) -> List[TripPattern]:
    print("function: combine_pt")
    trip_patterns: List[TripPattern] = []
    for i, (base, new_patterns) in enumerate(zip(base_patterns, results)):
        if validity is not None and not validity[i]:
            continue
        if len(new_patterns) == 0 and keep_base:
            trip_patterns.append(base)
        else:
            for np in new_patterns:
                combined = deepcopy(base)
                if arrive_by:
                    new_legs = deepcopy(np["legs"])
                    new_modes = deepcopy(np.get("modes", []))
                    if first_pt:
                        if combination:
                            justify_time(combined, new_legs[-1]["aimedEndTime"], False)
                        else:
                            justify_time({"aimedEndTime": "", "legs": new_legs}, base["legs"][0]["aimedStartTime"], True)
                    new_legs.extend(deepcopy(combined["legs"]))
                    new_modes.extend(deepcopy(combined.get("modes", [])))
                    combined["legs"] = new_legs
                    combined["modes"] = new_modes
                else:
                    if first_pt:
                        justify_time(combined, np["legs"][0]["aimedStartTime"], True)
                    combined["legs"].extend(np["legs"])
                    combined["aimedEndTime"] = np["aimedEndTime"]
                    combined["modes"] = combined.get("modes", []) + np.get("modes", [])
                trip_patterns.append(combined)
    return trip_patterns

def create_waypoint_groups(waypoints: List[str], pref: List[LegPreferences], multimodal: bool = True, mode: str = "") -> tuple[List[WaypointGroup], bool]:
    print("function: create_waypoint_groups")
    if not multimodal:
        return [{"group": waypoints, "mode": mode}], False

    groups: List[WaypointGroup] = []
    bike_segment_found = False
    i = 0
    while i < len(waypoints) - 1:
        group = [waypoints[i], waypoints[i + 1]]
        mode = pref[i].mode if i < len(pref) else None
        j = i
        if mode == "bicycle":
            bike_segment_found = True
        while j < len(pref) - 1 and pref[j + 1].mode == mode:
            group.append(waypoints[j + 2])
            j += 1
        groups.append({"group": group, "mode": mode})
        i = j + 1

    return groups, bike_segment_found

def filter_sort_trip_patterns(trip_patterns: List[TripPattern], data: RouteData) -> List[TripPattern]:
    print("function: filter_sort_trip_patterns")
    new_patterns: List[TripPattern] = []
    max_bike_distance = data.max_bike_distance if data.use_own_bike else data.max_bikesharing_distance
    foot_in_pref = (any(lp.mode == "foot" for lp in data.leg_preferences) and data.mode == "transit,bicycle,walk") or data.mode == "foot"
    for pattern in trip_patterns:
        if pattern.get("numOfTransfers", 0) > data.max_transfers:
            continue
        if "walkDistance" in pattern and pattern["walkDistance"] > data.max_walk_distance * 1000 + 50:
            if foot_in_pref:
                pattern["tooLongWalkDistance"] = True  
            else:
                continue
        if "bikeDistance" in pattern and pattern["bikeDistance"] > max_bike_distance * 1000 + 50:
            pattern["tooLongBikeDistance"] = True
        new_patterns.append(pattern)

    if data.route_preference == "shortest":
        sorted_patterns = sorted(new_patterns, key=lambda tp: tp.get("totalDistance", float("inf")))
    elif data.route_preference == "transfers":
        sorted_patterns = sorted(new_patterns, key=lambda tp: ("numOfTransfers" in tp, tp.get("numOfTransfers", 0)))
    else:
        if data.arrive_by:
            sorted_patterns = sorted(new_patterns, key=lambda tp: tp["legs"][0]["aimedStartTime"], reverse=True)
        else:
            sorted_patterns = sorted(new_patterns, key=lambda tp: tp["aimedEndTime"])
    
    return sorted_patterns[:10]
