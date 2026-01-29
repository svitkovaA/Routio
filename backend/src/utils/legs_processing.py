"""
file: legs_processing.py

Processing trip legs, including:
- adjusting start and end times of trip legs 
- merging consecutive legs with the same transport mode
- inserting transfer legs between different public transport services,
    computing accumulated parameters for visualisation
"""

from copy import deepcopy
from datetime import datetime, timedelta
from models.types import Leg, ServiceJourney, TripPattern, VehiclePositions
from typing import Optional, List

# Default route colors based on transport mode (used when route colors are not provided either from Lissy nor GTFS)
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
    Adjust start and end times of all legs in a trip pattern
    based on a target departure or arrival time

    Args:
        pattern: The trip pattern containing legs and aimed times
        time_to_depart: Datetime representing the target departure time 
            (if arrive_by=False) or arrival time (if arrive_by=True)
        arrive_by: If True, the provided time time_to_depart is treated as the
            arrival time, if false, the provided time is treated as the departure time

    Returns:
        None
    """
    print("function: justify_time")
    legs = pattern["legs"]

    # Convert date in ISO format to datetime
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
        
        # Assign the current known time
        legs[index][first] = time_to_depart_dt.isoformat()

        # Shift time according to leg duration
        if arrive_by:
            time_to_depart_dt -= timedelta(seconds=legs[index]["duration"])
        else:
            time_to_depart_dt += timedelta(seconds=legs[index]["duration"])
        legs[index][second] = time_to_depart_dt.isoformat()
        i += 1

    # Shift the final aimed end time for departure planning
    if not arrive_by:
        pattern["aimedEndTime"] = time_to_depart_dt.isoformat()

def merge_legs(leg1: Leg, leg2: Leg) -> Leg:
    """
    Merge two consecutive legs into a single new one
    
    Args:
        leg1: The first leg of the trip
        leg2: The second leg of the trip

    Returns:
        A new leg representing the merged result
    """
    print("function: merge_legs")
    merged_service_journey: Optional[ServiceJourney] = None

    service_journey_1 = leg1.get("serviceJourney")
    service_journey_2 = leg2.get("serviceJourney")

    # Merge service journey information
    if service_journey_1 and service_journey_2:
        merged_service_journey = {
            "quays": (
                service_journey_1["quays"]
                + [{"id": "", "name": service_journey_1["direction"]}]
                + service_journey_2["quays"]
            ),
            "direction": service_journey_1["direction"],
            "passingTimes": []
        }

    # Extract points on route from both legs
    points_1 = leg1["pointsOnLink"]["points"]
    points_2 = leg2["pointsOnLink"]["points"]

    merged_points: List[str] = []

    # Add a single point or extend the list with multiple points
    if isinstance(points_1, str):
        merged_points.append(points_1)
    else:
        merged_points.extend(points_1)

    if isinstance(points_2, str):
        merged_points.append(points_2)
    else:
        merged_points.extend(points_2)

    # Create merged leg
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

    # Preserve data from the original legs
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
    """
    The function merges consecutive legs with the same transport mode,
    inserts transfer legs between different public transport services 
    and computes accumulated parameters for visualisation 

    Args:
        pattern: Trip pattern containing a list of legs to be processed

    Returns:
        None
    """
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
    modes = pattern.get("modes") or []
    vehiclePositions: List[VehiclePositions] = []

    for leg in legs:
        # Assign default color based on transport mode (used when route color is not provided from Lissy or GTFS)
        if not leg.get("color"):
            leg["color"] = COLORS.get(leg["mode"], "gray")

        # Append information necessary for vehicle position visualisation
        if "tripId" in leg:
            vehiclePositions.append({
                "tripId": leg["tripId"], 
                "publicCode": leg["line"]["publicCode"],
                "color": leg["color"],
                "mode": leg["mode"],
                "lat": -1,
                "lon": -1,
                "direction": leg["otherOptions"]["departures"][leg["otherOptions"]["currentIndex"]]["direction"]
            })

        # Waypoint found between foot/bicycle segments
        if mode == leg["mode"] and mode in ["foot", "bicycle"]:
            mode_index += 1

        # Set true to walkmode if foot segment, false if transfer segment
        if leg["mode"] == "foot":
            leg["walkMode"] = mode_index < len(modes) and modes[mode_index] == "foot"

        # Join legs for the same public transport services when riding
        # through the final destination stop and continuing on the same line
        leg_public_code = (leg.get("line") or {}).get("publicCode")
        if prev_leg and leg["mode"] == mode and leg_public_code == public_code and leg_public_code:
            prev_leg = merge_legs(prev_leg, leg)
        else:
            if prev_leg:
                new_legs.append(prev_leg)
            prev_leg = leg
            public_code = leg_public_code

        mode = leg["mode"]

    # Append the last leg
    if prev_leg:
        new_legs.append(prev_leg)
    legs = new_legs
            
    original_legs = deepcopy(legs)

    # Insert transfer legs between different public transport services
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

    # Compute accumulated parameters used for visualisation
    for leg in legs[1:]:
        if leg["mode"] == "bicycle":
            bike_distance += leg["distance"]
        if leg["mode"] == "foot":
            walk_distance += leg["distance"]

        # Two consecutive walk/bicycle legs 
        if leg["mode"] == currentLeg["mode"] and leg["mode"] in ["foot", "bicycle"]:
            currentLeg["duration"] += leg["duration"]
            currentLeg["distance"] += leg["distance"]
            currentLeg["aimedEndTime"] = leg["aimedEndTime"]

            # Update the final place of current leg
            if "toPlace" in leg:
                currentLeg["toPlace"] = leg["toPlace"]

            # Create list with the first polyline
            if isinstance(currentLeg["pointsOnLink"]["points"], str):
                currentLeg["pointsOnLink"]["points"] = [currentLeg["pointsOnLink"]["points"]]

            # Append new polyline
            if "pointsOnLink" in leg:
                points = leg["pointsOnLink"]["points"]
                if isinstance(points, str):
                    currentLeg["pointsOnLink"]["points"].append(points)
                else:
                    currentLeg["pointsOnLink"]["points"].extend(points)

        else:
            # Public transport leg found
            if currentLeg["mode"] not in ["foot", "bicycle", "wait"]:
                num_of_transfers = num_of_transfers + 1 if num_of_transfers else 1
            currentLeg["accumulatedDuration"] = duration
            mergedLegs.append(currentLeg)
            duration += currentLeg["duration"]
            distance += currentLeg["distance"]
            currentLeg = deepcopy(leg)
    
    # Final leg processing if public transport
    if currentLeg["mode"] not in ["foot", "bicycle"]:
        num_of_transfers = num_of_transfers + 1 if num_of_transfers else 1

    currentLeg["accumulatedDuration"] = duration
    mergedLegs.append(currentLeg)

    duration += currentLeg["duration"]
    distance += currentLeg["distance"]

    # Store computed results into the pattern
    pattern["legs"] = mergedLegs
    pattern["polyInfo"] = []
    pattern["totalDuration"] = duration
    pattern["totalDistance"] = distance
    pattern["bikeDistance"] = bike_distance
    pattern["walkDistance"] = walk_distance
    pattern["vehiclePositions"] = vehiclePositions

    if num_of_transfers:
        pattern["numOfTransfers"] = num_of_transfers - 1

    pattern["originalLegs"] = original_legs

# End of file legs_processing.py
