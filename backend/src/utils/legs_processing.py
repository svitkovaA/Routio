from copy import deepcopy
from datetime import datetime, timedelta
from models.types import Leg, ServiceJourney, TripPattern
from typing import Optional, List

COLORS = {
    "foot": "blue",
    "bicycle": "red",
    "bus": "purple",
    "tram": "green",
    "trolleybus": "yellow",
    "rail": "orange",
}

def justify_time(pattern: TripPattern, time_to_depart: str, arrive_by: bool) -> None:
    """
    Justify the start and end times of all legs in a trip pattern
    based on a target departure or arrival time

    Args:
        pattern: The trip pattern containing legs and aimed times
        time_to_depart: Datetime representing the target departure time 
        (if arrive_by=False) or arrival time (if arrive_by=True)
        arrive_by: If True, the provided time time_to_depart is treated as the
        arrival time, if false, the provided time is treated as the departure time

    Returns:
        None: The function mutates the input trip pattern in place, updating all
        aimedStartTime and aimedEndTime values.
    """
    print("function: justify_time")
    legs = pattern["legs"]

    # COnvert date in ISO format to datetime
    time_to_depart_dt = datetime.fromisoformat(time_to_depart)
    if arrive_by:
        indecies = list(reversed(range(len(legs))))
        second = "aimedStartTime"
        first = "aimedEndTime"
        pattern["aimedEndTime"] = time_to_depart_dt.isoformat()
    else:
        indecies = list(range(len(legs)))
        first = "aimedStartTime"
        second = "aimedEndTime"

    # Process each leg and update times
    i = 0
    while i < len(indecies):
        index = indecies[i]
        
        # Assign the current known time as either start or end
        legs[index][first] = time_to_depart_dt.isoformat()
        if arrive_by:
            time_to_depart_dt -= timedelta(seconds=legs[index]["duration"])
        else:
            time_to_depart_dt += timedelta(seconds=legs[index]["duration"])
        legs[index][second] = time_to_depart_dt.isoformat()
        i += 1
    if not arrive_by:
        pattern["aimedEndTime"] = time_to_depart_dt.isoformat()

def merge_legs(leg1: Leg, leg2: Leg) -> Leg:
    print("function: merge_legs")
    merged_service_journey: Optional[ServiceJourney] = None
    service_journey_1 = leg1.get("serviceJourney")
    service_journey_2 = leg2.get("serviceJourney")
    if service_journey_1 and service_journey_2:
        merged_service_journey = {
            "quays": (
                service_journey_1["quays"]
                + [{"id": "", "name": service_journey_1["direction"]}]
                + service_journey_2["quays"]
            ),
            "direction": service_journey_1["direction"],
        }
    points_1 = leg1["pointsOnLink"]["points"]
    points_2 = leg2["pointsOnLink"]["points"]

    merged_points: List[str] = []

    if isinstance(points_1, str):
        merged_points.append(points_1)
    else:
        merged_points.extend(points_1)

    if isinstance(points_2, str):
        merged_points.append(points_2)
    else:
        merged_points.extend(points_2)
    merged: Leg = {
        "mode": leg1["mode"],
        "aimedStartTime": leg1["aimedStartTime"],
        "aimedEndTime": leg2["aimedEndTime"],
        "distance": leg1["distance"] + leg2["distance"],
        "duration": leg1["duration"] + leg2["duration"],
        "pointsOnLink": {
            "points": merged_points
        },
    }
    if "fromPace" in leg1:
        merged["fromPlace"] = leg1["fromPlace"]
    if "toPlace" in leg2:
        merged["toPlace"] = leg2["toPlace"]
    if "color" in leg1:
        merged["color"] = leg1["color"]
    if "line" in leg1:
        merged["line"] = leg1["line"]
    if merged_service_journey:
        merged["serviceJourney"] = merged_service_journey
    if "otherOptions" in leg1:
        merged["otherOptions"] = leg1["otherOptions"]
    return merged

def process_legs(pattern: TripPattern) -> None:
    print("function: process_legs")
    if not pattern or not pattern.get("legs"):
        return
    
    legs = pattern["legs"]
    mergedLegs: List[Leg] = []
    duration = 0
    distance = 0
    num_of_transfers = None

    mode_index = 0
    mode = ""
    public_code = ""
    new_legs: List[Leg] = []
    prev_leg = None
    for leg in legs:
        if not leg.get("color"):
            leg["color"] = COLORS.get(leg["mode"], "gray")
        if mode == leg["mode"] and mode in ["foot", "bicycle"]:
            mode_index += 1
        if leg["mode"] == "foot":
            modes = pattern.get("modes") or []
            leg["walkMode"] = mode_index < len(modes) and modes[mode_index] == "foot"
        leg_public_code = (leg.get("line") or {}).get("publicCode")

        if prev_leg and leg["mode"] == mode and leg_public_code == public_code and leg_public_code:
            prev_leg = merge_legs(prev_leg, leg)
        else:
            if prev_leg:
                new_legs.append(prev_leg)
            prev_leg = leg
            public_code = leg_public_code

        mode = leg["mode"]

    if prev_leg:
        new_legs.append(prev_leg)
    legs = new_legs
            
    original_legs = deepcopy(legs)

    mode = "foot"
    i = 0
    while i < len(original_legs):
        leg = original_legs[i]

        if leg["mode"] not in ["foot", "bicycle", "wait"] and mode not in ["foot", "bicycle", "wait"]:
            new_leg: Leg = {
                "mode": "transfer",
                "aimedStartTime": "",
                "aimedEndTime": "",
                "color": "gray",
                "distance": 0,
                "duration": 0,
                "accumulatedDuration": 0,
                "pointsOnLink": {
                    "points": []
                }
            }
            original_legs.insert(i, new_leg)
            i += 1

        mode = leg["mode"]
        i += 1

    currentLeg = deepcopy(legs[0])
    bike_distance = currentLeg["distance"] if currentLeg["mode"] == "bicycle" else 0
    walk_distance = currentLeg["distance"] if currentLeg["mode"] == "foot" else 0

    for leg in legs[1:]:
        if leg["mode"] == "bicycle":
            bike_distance += leg["distance"]
        if leg["mode"] == "foot":
            walk_distance += leg["distance"]
        if leg["mode"] == currentLeg["mode"] and leg["mode"] in ["foot", "bicycle"]:
            currentLeg["duration"] += leg["duration"]
            currentLeg["distance"] += leg["distance"]
            currentLeg["aimedEndTime"] = leg["aimedEndTime"]
            if "toPlace" in leg:
                currentLeg["toPlace"] = leg["toPlace"]
            if isinstance(currentLeg["pointsOnLink"]["points"], str):
                currentLeg["pointsOnLink"]["points"] = [currentLeg["pointsOnLink"]["points"]]

            if "pointsOnLink" in leg:
                points = leg["pointsOnLink"]["points"]
                if isinstance(points, str):
                    currentLeg["pointsOnLink"]["points"].append(points)
                else:
                    currentLeg["pointsOnLink"]["points"].extend(points)

        else:
            if currentLeg["mode"] not in ["foot", "bicycle", "wait"]:
                num_of_transfers = num_of_transfers + 1 if num_of_transfers else 1
            currentLeg["accumulatedDuration"] = duration

            mergedLegs.append(currentLeg)
            duration += currentLeg["duration"]
            distance += currentLeg["distance"]

            currentLeg = deepcopy(leg)
    
    if currentLeg["mode"] not in ["foot", "bicycle"]:
        num_of_transfers = num_of_transfers + 1 if num_of_transfers else 1
    currentLeg["accumulatedDuration"] = duration
    mergedLegs.append(currentLeg)
    duration += currentLeg["duration"]
    distance += currentLeg["distance"]

    pattern["legs"] = mergedLegs

    pattern["polyInfo"] = []
    pattern["totalDuration"] = duration
    pattern["totalDistance"] = distance
    pattern["bikeDistance"] = bike_distance
    pattern["walkDistance"] = walk_distance
    if num_of_transfers:
        pattern["numOfTransfers"] = num_of_transfers - 1
    pattern["originalLegs"] = original_legs
