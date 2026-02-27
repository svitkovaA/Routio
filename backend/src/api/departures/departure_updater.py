from datetime import timedelta
from typing import List
from fastapi import HTTPException
from shared.pattern_utils import PatternUtils
from models.route import Leg, TripPattern, VehiclePositions
from models.departure_data import DepartureData

class DepartureUpdater():
    @staticmethod
    def update_departures(data: DepartureData) -> TripPattern:
        index = data.public_leg_index
        legs = data.trip_pattern.originalLegs

        DepartureUpdater.__update_selected_leg(data, index, legs)
        DepartureUpdater.__propagate_times(index, legs)
        DepartureUpdater.__update_vehicle_positions(data)
        DepartureUpdater.__update_final_end_time(data)

        return data.trip_pattern

    @staticmethod
    def __update_selected_leg(
        data: DepartureData,
        index: int,
        legs: List[Leg]
    ) -> None:

        leg = legs[index]

        if not leg.otherOptions or not leg.serviceJourney:
            raise HTTPException(
                status_code=400,
                detail="Missing serviceJourney or otherOptions"
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

        DepartureUpdater.__propagate_backwards_if_needed(index, legs)

    @staticmethod
    def __propagate_backwards_if_needed(
        index: int,
        legs: List[Leg]
    ) -> None:
        without_public_transport = True

        for i in range(index - 1):
            if legs[i].mode not in ["bicycle", "foot", "wait", "transfer"]:
                without_public_transport = False

        if without_public_transport:
            PatternUtils.justify_time(
                TripPattern(legs=legs[:index]),
                legs[index].aimedStartTime,
                True
            )
        else:
            if legs[index - 1].aimedEndTime > legs[index].aimedStartTime:
                legs[index].arrivalAfterDeparture = True

    @staticmethod
    def __propagate_times(
        start_index: int,
        legs: List[Leg]
    ) -> None:
        index = start_index + 1

        while index < len(legs):
            leg = legs[index]
            previous_leg = legs[index - 1]

            if leg.mode in ["foot", "bicycle", "wait", "transfer"]:
                leg.aimedStartTime = previous_leg.aimedEndTime
            else:
                DepartureUpdater.__select_next_valid_departure(leg, previous_leg)

            leg.aimedEndTime = (
                leg.aimedStartTime +
                timedelta(seconds=leg.duration)
            )

            index += 1

    @staticmethod
    def __select_next_valid_departure(
        leg: Leg,
        previous_leg: Leg
    ) -> None:
        if not leg.otherOptions or not leg.serviceJourney:
            raise HTTPException(
                status_code=400,
                detail="Missing serviceJourney or otherOptions"
            )

        deps = leg.otherOptions.departures
        picked_i = None

        for i, departure in enumerate(deps):
            if departure.departureTime >= previous_leg.aimedEndTime:
                picked_i = i
                leg.aimedStartTime = departure.departureTime
                leg.otherOptions.currentIndex = i
                leg.serviceJourney.direction = departure.direction
                leg.tripId = departure.tripId
                break

        leg.arrivalAfterDeparture = False
        leg.nonContinuousDepartures = False

        if picked_i is None and deps:
            last = deps[-1]
            leg.aimedStartTime = last.departureTime
            leg.otherOptions.currentIndex = len(deps) - 1
            leg.serviceJourney.direction = last.direction
            leg.nonContinuousDepartures = True

    @staticmethod
    def __update_vehicle_positions(data: DepartureData) -> None:

        vehicle_positions: List[VehiclePositions] = []

        for leg in data.trip_pattern.originalLegs:
            if (
                leg.tripId
                and leg.line
                and leg.color
                and leg.otherOptions
                and leg.otherOptions.currentIndex is not None
            ):
                vehicle_positions.append(
                    VehiclePositions(
                        tripId=leg.tripId,
                        publicCode=leg.line.publicCode,
                        color=leg.color,
                        mode=leg.mode,
                        lat=-1,
                        lon=-1,
                        direction=leg.otherOptions.departures[
                            leg.otherOptions.currentIndex
                        ].direction
                    )
                )

        data.trip_pattern.vehiclePositions = vehicle_positions

    @staticmethod
    def __update_final_end_time(data: DepartureData) -> None:
        legs = data.trip_pattern.originalLegs
        data.trip_pattern.aimedEndTime = legs[-1].aimedEndTime
