from copy import deepcopy
from datetime import datetime, timedelta

COLORS = {
    "foot": "blue",
    "bicycle": "red",
    "bus": "purple",
    "tram": "green",
    "trolleybus": "yellow",
    "rail": "orange",
}

def justify_time(pattern, time_to_depart: str, arrive_by: bool):
    print("function: justify_time")
    legs = pattern["legs"]
    time_to_depart = datetime.fromisoformat(time_to_depart)
    if arrive_by:
        indecies = list(reversed(range(len(legs))))
        second = "aimedStartTime"
        first = "aimedEndTime"
        pattern["aimedEndTime"] = time_to_depart.isoformat()
    else:
        indecies = list(range(len(legs)))
        first = "aimedStartTime"
        second = "aimedEndTime"
    i = 0
    while i < len(indecies):
        index = indecies[i]
        
        legs[index][first] = time_to_depart.isoformat()
        if arrive_by:
            time_to_depart -= timedelta(seconds=legs[index]["duration"])
        else:
            time_to_depart += timedelta(seconds=legs[index]["duration"])
        legs[index][second] = time_to_depart.isoformat()
        i += 1
    if not arrive_by:
        pattern["aimedEndTime"] = time_to_depart.isoformat()

def merge_legs(leg1: dict, leg2: dict) -> dict:
    print("function: merge_legs")
    merged = {
        "mode": leg1["mode"],
        "aimedStartTime": leg1["aimedStartTime"],
        "aimedEndTime": leg2["aimedEndTime"],
        "distance": leg1["distance"] + leg2["distance"],
        "duration": leg1["duration"] + leg2["duration"],
        "fromPlace": leg1["fromPlace"],
        "toPlace": leg2["toPlace"],
        "line": leg1["line"],
        "serviceJourney": {
            "quays": leg1["serviceJourney"]["quays"] + [{"name": leg1["serviceJourney"]["direction"]}] + leg2["serviceJourney"]["quays"],
            "direction": leg1["serviceJourney"]["direction"]
        },
        "pointsOnLink": {
            "points": [leg1["pointsOnLink"]["points"], leg2["pointsOnLink"]["points"]]
        },
        "color": leg1["color"],
        "otherOptions": leg1["otherOptions"]
    }
    return merged

def process_legs(pattern):
    print("function: process_legs")
    if not pattern or not pattern.get("legs"):
        return
    
    legs = pattern["legs"]
    mergedLegs = []
    duration = 0
    distance = 0
    num_of_transfers = None

    mode_index = 0
    mode = ""
    public_code = ""
    new_legs = []
    prev_leg = None
    for leg in legs:
        if not leg.get("color"):
            leg["color"] = COLORS.get(leg["mode"], "gray")
        if mode == leg["mode"] and mode in ["foot", "bicycle"]:
            mode_index += 1
        if leg["mode"] == "foot":
            leg["walkMode"] = pattern["modes"][mode_index] == "foot"
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
            new_leg = {
                "mode": "transfer",
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
            currentLeg["toPlace"] = leg["toPlace"]
            if isinstance(currentLeg["pointsOnLink"]["points"], str):
                currentLeg["pointsOnLink"]["points"] = [currentLeg["pointsOnLink"]["points"]]

            currentLeg["pointsOnLink"]["points"].append(leg["pointsOnLink"]["points"])

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
