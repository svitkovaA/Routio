"""
file: departures.py

API endpoint for handling alternative public transport departures.
"""

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, HTTPException
from models.route import TripPattern, VehiclePositions
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
    legs = data.trip_pattern.originalLegs
    leg = legs[index]
    
    # Check if the legs before the selected index contains public transport mode
    without_public_transport = True
    for i in range(index - 1):
        if legs[i].mode not in ["bicycle", "foot", "wait", "transfer"]:
            without_public_transport = False

    if not leg.otherOptions or not leg.serviceJourney:
        raise HTTPException(
            status_code = 400,
            detail = "Missing serviceJourney or otherOptions"
        )

    # Update selected public transport leg
    chosen_dep = leg.otherOptions.departures[data.selected_index]
    leg.aimedStartTime = chosen_dep.departureTime
    leg.otherOptions.currentIndex = data.selected_index
    leg.serviceJourney.direction = chosen_dep.direction
    leg.tripId = chosen_dep.tripId

    # Compute end time of the selected leg
    leg.aimedEndTime = leg.aimedStartTime + timedelta(seconds=leg.duration)

    # Validate arrival/departure continuity
    leg.arrivalAfterDeparture = False

    # Propagate timing backwards if no public transport precedes this leg
    if without_public_transport:
        justify_time(
            TripPattern(
                legs=legs[:index],
                aimedEndTime=datetime.min
            ),
            leg.aimedStartTime, 
            True
        )
    else:
        # Detection of arrival later than selected departure
        if legs[index - 1].aimedEndTime > legs[index].aimedStartTime:
            legs[index].arrivalAfterDeparture = True
    index += 1

    # Shift all next legs
    while index < len(legs):
        leg = legs[index]

        # If the current leg is not public transport, set the aimed start time to previous leg end time
        if leg.mode in ["foot", "bicycle", "wait", "transfer"]:
            leg.aimedStartTime = legs[index - 1].aimedEndTime
        else:
            # Get other possible departures of the selected public transport service
            deps = leg.otherOptions.departures if leg.otherOptions else []

            if not leg.otherOptions or not leg.serviceJourney:
                raise HTTPException(
                    status_code = 400,
                    detail = "Missing serviceJourney or otherOptions"
                )

            # Select the first valid departure after previous leg end
            picked_i = None
            for i, departure in enumerate(deps):
                if departure.departureTime >= legs[index - 1].aimedEndTime:
                    picked_i = i
                    leg.aimedStartTime = departure.departureTime
                    leg.otherOptions.currentIndex = i
                    leg.serviceJourney.direction = departure.direction
                    leg.tripId = departure.tripId
                    break

            leg.arrivalAfterDeparture = False
            leg.nonContinuousDepartures = False

            # If no valid departure is found, select the last available one
            if picked_i is None and deps:
                last = deps[-1]
                leg.aimedStartTime = last.departureTime
                leg.otherOptions.currentIndex = len(deps) - 1
                leg.serviceJourney.direction = last.direction
                leg.nonContinuousDepartures = True

        # Compute end time of the current leg 
        leg.aimedEndTime = leg.aimedStartTime + timedelta(seconds=leg.duration)

        index += 1

    # Store information about vehicle position for visualisation
    vehicle_positions: List[VehiclePositions] = []
    for leg in data.trip_pattern.originalLegs:
        if leg.tripId and leg.line and leg.color and leg.otherOptions and leg.otherOptions.currentIndex is not None:
                vehicle_positions.append(VehiclePositions(
                    tripId=leg.tripId,
                    publicCode=leg.line.publicCode,
                    color=leg.color,
                    mode=leg.mode,
                    lat=-1,
                    lon=-1,
                    direction=leg.otherOptions.departures[leg.otherOptions.currentIndex].direction
                ))

    data.trip_pattern.vehiclePositions = vehicle_positions

    # Update final trip end time
    data.trip_pattern.aimedEndTime = legs[-1].aimedEndTime

    return data.trip_pattern

# End of file departures.py
