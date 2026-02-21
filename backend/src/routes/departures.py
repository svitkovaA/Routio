"""
file: departures.py

API endpoint for handling alternative public transport departures.
"""

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter
from models.types import VehiclePositions
from models.departure_data import DepartureData
from utils.legs_processing import justify_time

router = APIRouter()

@router.post("/otherDepartures")
async def other_departures(data: DepartureData):
    """
    Update a trip pattern after the selection of an alternative public transport departure

    Args:
        data: Object containing trip pattern data and selected departure index

    Returns:
        Updated trip pattern with adjusted leg timings
    """
    print("endpoint: other_departures")
    index = data.public_leg_index
    legs = data.trip_pattern["originalLegs"]
    
    # Check if the legs before the selected index contains public transport mode
    without_public_transport = True
    for i in range(index - 1):
        if legs[i]["mode"] not in ["bicycle", "foot", "wait", "transfer"]:
            without_public_transport = False

    # Update selected public transport leg
    chosen_dep = legs[index]["otherOptions"]["departures"][data.selected_index]
    legs[index]["aimedStartTime"] = chosen_dep["departureTime"]
    legs[index]["otherOptions"]["currentIndex"] = data.selected_index
    legs[index]["serviceJourney"]["direction"] = chosen_dep["direction"]
    legs[index]["tripId"] = chosen_dep["tripId"]

    # Compute end time of the selected leg
    start_dt = datetime.fromisoformat(legs[index]["aimedStartTime"])
    legs[index]["aimedEndTime"] = (start_dt + timedelta(seconds=legs[index]["duration"])).isoformat()

    # Validate arrival/departure continuity
    legs[index]["arrivalAfterDeparture"] = False

    # Propagate timing backwards if no public transport precedes this leg
    if without_public_transport:
        justify_time({"legs": legs[:index], "aimedEndTime": ""}, legs[index]["aimedStartTime"], True)
    else:
        # Detection of arrival later than selected departure
        if legs[index - 1]["aimedEndTime"] > legs[index]["aimedStartTime"]:
            legs[index]["arrivalAfterDeparture"] = True
    index += 1

    # Shift all next legs
    while index < len(legs):
        # Get the aimed end time of the previous leg
        prev_end_dt = datetime.fromisoformat(legs[index - 1]["aimedEndTime"])

        # If the current leg is not public transport, set the aimed start time to previous leg end time
        if legs[index]["mode"] in ["foot", "bicycle", "wait", "transfer"]:
            legs[index]["aimedStartTime"] = prev_end_dt.isoformat()
        else:
            # Get other possible departures of the selected public transport service
            deps = legs[index].get("otherOptions", {}).get("departures", [])

            # Select the first valid departure after previous leg end
            picked_i = None
            for i, departure in enumerate(deps):
                dep_dt = datetime.fromisoformat(departure["departureTime"])
                if dep_dt >= prev_end_dt:
                    picked_i = i
                    legs[index]["aimedStartTime"] = departure["departureTime"]
                    legs[index]["otherOptions"]["currentIndex"] = i
                    legs[index]["serviceJourney"]["direction"] = departure["direction"]
                    legs[index]["tripId"] = departure["tripId"]
                    break

            legs[index]["arrivalAfterDeparture"] = False
            legs[index]["nonContinuousDepartures"] = False

            # If no valid departure is found, select the last available one
            if picked_i is None and deps:
                last = deps[-1]
                legs[index]["aimedStartTime"] = last["departureTime"]
                legs[index]["otherOptions"]["currentIndex"] = len(deps) - 1
                legs[index]["serviceJourney"]["direction"] = last["direction"]
                legs[index]["nonContinuousDepartures"] = True

        # Compute end time of the current leg 
        start_dt = datetime.fromisoformat(legs[index]["aimedStartTime"])
        legs[index]["aimedEndTime"] = (start_dt + timedelta(seconds=legs[index]["duration"])).isoformat()

        index += 1

    # Store information about vehicle position for visualisation
    vehicle_positions: List[VehiclePositions] = []
    for leg in data.trip_pattern["originalLegs"]:
        if "tripId" in leg and "line" in leg and "color" in leg and "otherOptions" in leg and leg["otherOptions"]["currentIndex"] is not None:
                vehicle_positions.append({
                    "tripId": leg["tripId"], 
                    "publicCode": leg["line"]["publicCode"],
                    "color": leg["color"],
                    "mode": leg["mode"],
                    "lat": -1,
                    "lon": -1,
                    "direction": leg["otherOptions"]["departures"][leg["otherOptions"]["currentIndex"]]["direction"]
                })

    data.trip_pattern["vehiclePositions"] = vehicle_positions

    # Update final trip end time
    data.trip_pattern["aimedEndTime"] = legs[-1]["aimedEndTime"]

    return data.trip_pattern

# End of file departures.py
