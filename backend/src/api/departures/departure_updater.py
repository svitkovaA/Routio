"""
file: departure_updater.py

Contains logic for recalculating a trip pattern when a user selects a different
public transport departure option.
"""

from datetime import datetime, timedelta
from typing import List
from fastapi import HTTPException
from shared.leg_utils import LegUtils
from shared.pattern_utils import PatternUtils
from models.route import TIME_DEPENDENT_MODES, TZ, Leg, TripPattern, VehicleRealtimeData
from models.departure_data import DepartureData

class DepartureUpdater():
    """
    Handles recalculation of trip pattern after departure change.
    """
    @staticmethod
    def update_departures(data: DepartureData) -> TripPattern:
        """
        Entry point for updating a trip pattern after departure change.

        Args:
            data: Request payload

        Returns:
            Updated trip pattern
        """
        index = data.public_leg_index
        legs = data.trip_pattern.originalLegs

        # Update selected public transport leg
        DepartureUpdater.__update_selected_leg(data, index, legs)

        # Propagate time adjustments
        DepartureUpdater.__propagate_times(index, legs)

        # Update vehicle positions
        DepartureUpdater.__update_vehicle_positions(data)

        # Recalculate final trip end time
        DepartureUpdater.__update_final_end_time(data)

        # Postprocess trip pattern
        data.trip_pattern.legs = legs
        LegUtils.process_legs(data.trip_pattern)

        return data.trip_pattern

    @staticmethod
    def __update_selected_leg(
        data: DepartureData,
        index: int,
        legs: List[Leg]
    ) -> None:
        """
        Updates selected public transport leg with newly chosen departure.

        Args:
            data: Request payload containing updated departure selection
            index: Index of the public transport leg inside trip pattern
            legs: List of original legs to be modified
        """
        # Target public transport leg
        leg = legs[index]

        # Validate required public transport data
        if not leg.otherOptions or not leg.serviceJourney:
            raise HTTPException(
                status_code=400,
                detail="Missing serviceJourney or otherOptions"
            )

        # Update selected public transport leg
        chosen_dep = leg.otherOptions.departures[data.selected_index]

        # Update timing and other data
        leg.aimedStartTime = chosen_dep.departureTime
        leg.otherOptions.currentIndex = data.selected_index
        leg.serviceJourney.direction = chosen_dep.direction
        leg.tripId = chosen_dep.tripId

        # Compute updated end time and passing time
        DepartureUpdater.__update_times(leg)

        # Reset arrival/departure continuity flag
        leg.arrivalAfterDeparture = False

        # Adjust previous legs if necessary
        DepartureUpdater.__propagate_backwards_if_needed(index, legs)

    @staticmethod
    def __propagate_backwards_if_needed(
        index: int,
        legs: List[Leg]
    ) -> None:
        """
        Ensures time continuity before updated public transport leg.

        Args:
            index: Index of updated leg
            legs: List of legs in trip pattern
        """
        without_public_transport = True

        # Check if previous legs contain public transport
        for i in range(index - 1):
            if legs[i].mode not in ["bicycle", "foot", "wait", "transfer"]:
                without_public_transport = False

        # If no public transport before, justify entire previous segment
        if without_public_transport:
            PatternUtils.justify_time(
                TripPattern(legs=legs[:index]),
                legs[index].aimedStartTime,
                True
            )
        else:
            # Validate continuity between previous and current leg
            if legs[index - 1].aimedEndTime > legs[index].aimedStartTime:
                legs[index].arrivalAfterDeparture = True

    @staticmethod
    def __propagate_times(
        start_index: int,
        legs: List[Leg]
    ) -> None:
        """
        Propagates updated timing forward to subsequent legs.

        Args:
            start_index: Index of updated public transport leg
            legs: List of legs in trip pattern
        """
        # Start propagation from next leg
        index = start_index + 1

        while index < len(legs):
            leg = legs[index]
            previous_leg = legs[index - 1]

            # If non public transport, take previous end time
            if leg.mode in ["foot", "bicycle", "wait", "transfer"]:
                leg.aimedStartTime = previous_leg.aimedEndTime
            # Select next valid public transport departure
            else:
                DepartureUpdater.__select_next_valid_departure(leg, previous_leg)

            # Compute updated end time and passing time
            DepartureUpdater.__update_times(leg)

            # Move to next leg
            index += 1
    
    @staticmethod
    def __update_times(leg: Leg) -> None:
        """
        Computes new end time and passing time for public transport leg.

        Args:
            leg: The leg to be changed
        """
        # Compute the new end time based on the start time and leg duration
        new_end_time = leg.aimedStartTime + timedelta(seconds=leg.duration)

        # Determine how much the end time shifted compared to the original value
        time_delta = new_end_time - leg.aimedEndTime

        # Update the leg end time
        leg.aimedEndTime = new_end_time

        # Public transport leg
        if leg.mode in TIME_DEPENDENT_MODES and leg.serviceJourney:
            # Extract departure time string from passingTimes
            time_str = leg.serviceJourney.passingTimes[0]["departure"].time

            # Convert the time string to a datetime
            new_time = datetime.combine(
                leg.aimedStartTime.date(),
                datetime.strptime(time_str, "%H:%M:%S").time()
            ) + time_delta

            # Store the updated time back as string
            leg.serviceJourney.passingTimes[0]["departure"].time = new_time.strftime("%H:%M:%S")

    @staticmethod
    def __select_next_valid_departure(
        leg: Leg,
        previous_leg: Leg
    ) -> None:
        """
        Selects earliest valid departure after previous leg arrival.

        Args:
            leg: Public transport leg to update
            previous_leg: Leg that precedes the current one
        """
        # Validate required public transport data
        if not leg.otherOptions or not leg.serviceJourney:
            raise HTTPException(
                status_code=400,
                detail="Missing serviceJourney or otherOptions"
            )

        # Available departures
        deps = leg.otherOptions.departures

        # Index of selected departure
        picked_i = None

        # Find earliest valid departure
        for i, departure in enumerate(deps):
            if departure.departureTime >= previous_leg.aimedEndTime:
                picked_i = i
                leg.aimedStartTime = departure.departureTime
                leg.otherOptions.currentIndex = i
                leg.serviceJourney.direction = departure.direction
                leg.tripId = departure.tripId
                break

        # Reset continuity flags
        leg.arrivalAfterDeparture = False
        leg.nonContinuousDepartures = False

        # If no valid future departure, use fallback to last available one
        if picked_i is None and deps:
            last = deps[-1]
            leg.aimedStartTime = last.departureTime
            leg.otherOptions.currentIndex = len(deps) - 1
            leg.serviceJourney.direction = last.direction
            leg.nonContinuousDepartures = True
            leg.tripId = last.tripId

    @staticmethod
    def __update_vehicle_positions(data: DepartureData) -> None:
        """
        Update vehicle real-time list after trip update.

        Args:
            data: Request payload containing updated trip pattern
        """
        # New vehicle list
        vehicle_positions: List[VehicleRealtimeData] = []

        # Iterate through updated legs
        for leg in data.trip_pattern.originalLegs:
            if (
                leg.tripId
                and leg.line
                and leg.color
                and leg.otherOptions
                and leg.otherOptions.currentIndex is not None
                and leg.serviceJourney
            ):
                # Extract scheduled departure time from the first stop
                time = datetime.strptime(leg.serviceJourney.passingTimes[0]["departure"].time, "%H:%M:%S").time()
                
                # Combine extracted time with the planned start date
                start_time = datetime.combine(leg.aimedStartTime.date(), time, tzinfo=TZ)

                vehicle_positions.append(
                    VehicleRealtimeData(
                        tripId=leg.tripId,
                        publicCode=leg.line.publicCode,
                        color=leg.color,
                        mode=leg.mode,
                        lat=-1,
                        lon=-1,
                        direction=leg.otherOptions.departures[
                            leg.otherOptions.currentIndex
                        ].direction,
                        startTime=start_time
                    )
                )

        # Replace vehicle list in trip pattern
        data.trip_pattern.vehicleRealtimeData = vehicle_positions

    @staticmethod
    def __update_final_end_time(data: DepartureData) -> None:
        """
        Updates final trip end time based on last leg.

        Args:
            data: Request payload containing updated trip pattern
        """
        legs = data.trip_pattern.originalLegs
        data.trip_pattern.aimedEndTime = legs[-1].aimedEndTime

# End of file departure_updater.py
