"""
file: legs_processing.py

Processing trip legs, including:
- adjusting start and end times of trip legs, 
- merging consecutive legs with the same transport mode,
- inserting transfer legs between different public transport services,
    computing accumulated parameters for visualisation.
"""

from copy import deepcopy
from datetime import datetime, timedelta
from models.route import Leg, Mode, PointOnLink, Quay, ServiceJourney, TripPattern, VehiclePositions
from typing import Optional, List

# Default route colors based on transport mode
COLORS = {
    "foot": "blue",
    "bicycle": "red"
}

def justify_time(pattern: TripPattern, time_to_depart: datetime, arrive_by: bool) -> None:
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
    
    legs = pattern.legs

    if arrive_by:
        leg_indices = reversed(range(len(legs)))
        pattern.aimedEndTime = time_to_depart
    else:
        leg_indices = range(len(legs))

    # Process each leg and update times
    for index in leg_indices:
        leg = legs[index]

        # Shift time according to leg duration
        if arrive_by:
            leg.aimedEndTime = time_to_depart
            time_to_depart -= timedelta(seconds=legs[index].duration)
            leg.aimedStartTime = time_to_depart
        else:
            leg.aimedStartTime = time_to_depart
            time_to_depart += timedelta(seconds=legs[index].duration)
            leg.aimedEndTime = time_to_depart

    # Shift the final aimed end time for departure planning
    if not arrive_by:
        pattern.aimedEndTime = time_to_depart

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

    service_journey_1 = leg1.serviceJourney
    service_journey_2 = leg2.serviceJourney

    # Merge service journey information
    if service_journey_1 and service_journey_2:
        merged_service_journey = ServiceJourney(
            quays=(
                service_journey_1.quays
                + [Quay(id="", name=service_journey_1.direction)]
                + service_journey_2.quays
            ),
            direction=service_journey_1.direction,
            passingTimes=[]
        )

    # Extract points on route from both legs
    points_1 = leg1.pointsOnLink.points
    points_2 = leg2.pointsOnLink.points

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
    return Leg(
        mode=leg1.mode,
        aimedStartTime=leg1.aimedStartTime,
        aimedEndTime=leg2.aimedEndTime,
        distance=leg1.distance + leg2.distance,
        duration=leg1.duration + leg2.duration,
        pointsOnLink=PointOnLink(
            points=merged_points
        ),
        fromPlace=leg1.fromPlace,
        toPlace=leg2.toPlace,
        color=leg1.color,
        line=leg1.line,
        serviceJourney=merged_service_journey,
        otherOptions=leg1.otherOptions
    )

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
    
    legs = pattern.legs
    mergedLegs: List[Leg] = []
    duration = 0
    distance = 0
    num_of_transfers = None

    mode_index = 0
    mode: Mode = "transfer"     # Dummy value
    public_code = ""
    new_legs: List[Leg] = []
    prev_leg = None
    modes = pattern.modes
    vehiclePositions: List[VehiclePositions] = []

    for leg in legs:
        # Assign default color based on transport mode (used when route color is not provided from Lissy or GTFS)
        if not leg.color:
            leg.color = COLORS.get(leg.mode, "black")

        # Append information necessary for vehicle position visualisation
        if leg.tripId and leg.line and leg.otherOptions and leg.otherOptions.currentIndex:
            vehiclePositions.append(
                VehiclePositions(
                    tripId=leg.tripId,
                    publicCode=leg.line.publicCode,
                    color=leg.color,
                    mode=leg.mode,
                    lat=-1, # Dummy value
                    lon=-1, # Dummy value
                    direction=leg.otherOptions.departures[leg.otherOptions.currentIndex].direction
                )
            )

        # Waypoint found between foot/bicycle segments
        if mode == leg.mode and mode in ["foot", "bicycle"]:
            mode_index += 1

        # Set true to walkmode if foot segment, false if transfer segment
        if leg.mode == "foot":
            leg.walkMode = mode_index < len(modes) and modes[mode_index] == "foot"

        # Join legs for the same public transport services when riding
        # through the final destination stop and continuing on the same line
        leg_public_code = leg.line.publicCode if leg.line else ""
        if prev_leg and leg.mode == mode and leg_public_code == public_code and leg_public_code:
            prev_leg = merge_legs(prev_leg, leg)
        else:
            if prev_leg:
                new_legs.append(prev_leg)
            prev_leg = leg
            public_code = leg_public_code

        mode = leg.mode

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

        if leg.mode not in ["foot", "bicycle", "wait"] and mode not in ["foot", "bicycle", "wait"]:
            new_leg = Leg(
                mode="transfer",
                aimedStartTime=datetime.min, # Dummy value
                aimedEndTime=datetime.min, # Dummy value
                color="gray",
                distance=0,
                duration=0,
                accumulatedDuration=0,
                pointsOnLink=PointOnLink(
                    points=[]
                )
            )

            original_legs.insert(i, new_leg)
            i += 1

        mode = leg.mode
        i += 1

    currentLeg = deepcopy(legs[0])
    bike_distance = currentLeg.distance if currentLeg.mode == "bicycle" else 0
    walk_distance = currentLeg.distance if currentLeg.mode == "foot" else 0

    # Compute accumulated parameters used for visualisation
    for leg in legs[1:]:
        if leg.mode == "bicycle":
            bike_distance += leg.distance
        if leg.mode == "foot":
            walk_distance += leg.distance

        # Two consecutive walk/bicycle legs
        if leg.mode == currentLeg.mode and leg.mode in ["foot", "bicycle"]:
            currentLeg.duration += leg.duration
            currentLeg.distance += leg.distance
            currentLeg.aimedEndTime = leg.aimedEndTime

            # Update the final place of current leg
            currentLeg.toPlace = leg.toPlace

            # Create list with the first polyline
            if isinstance(currentLeg.pointsOnLink.points, str):
                points = currentLeg.pointsOnLink.points
                currentLeg.pointsOnLink.points = [points]

            # Append new polyline
            if leg.pointsOnLink:
                points = leg.pointsOnLink.points
                if isinstance(points, str):
                    currentLeg.pointsOnLink.points.append(points)
                else:
                    currentLeg.pointsOnLink.points.extend(points)

        else:
            # Public transport leg found
            if currentLeg.mode not in ["foot", "bicycle", "wait"]:
                num_of_transfers = num_of_transfers + 1 if num_of_transfers else 1
            currentLeg.accumulatedDuration = duration
            mergedLegs.append(currentLeg)
            duration += currentLeg.duration
            distance += currentLeg.distance
            currentLeg = deepcopy(leg)
    
    # Final leg processing if public transport
    if currentLeg.mode not in ["foot", "bicycle"]:
        num_of_transfers = num_of_transfers + 1 if num_of_transfers else 1

    currentLeg.accumulatedDuration = duration
    mergedLegs.append(currentLeg)

    duration += currentLeg.duration
    distance += currentLeg.distance

    # Store computed results into the pattern
    pattern.legs = mergedLegs
    pattern.polyInfo = []
    pattern.totalDuration = duration
    pattern.totalDistance = distance
    pattern.bikeDistance = bike_distance
    pattern.walkDistance = walk_distance
    pattern.vehiclePositions = vehiclePositions

    if num_of_transfers:
        pattern.numOfTransfers = num_of_transfers - 1

    pattern.originalLegs = original_legs

# End of file legs_processing.py
