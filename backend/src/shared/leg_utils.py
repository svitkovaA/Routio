"""
file: leg_utils.py

Utilities responsible for post processing routing engine output
"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Literal, Optional
from models.route import (
    TIME_INDEPENDENT_MODES,
    TZ,
    PointOnLink, RoutingMode,
    ServiceJourney,
    Quay,
    Leg,
    TripPattern,
    Mode,
    VehicleRealtimeData
)

@dataclass
class _LegStats:
    """
    Internal data structure holding aggregated route statistics computed during
    leg post processing.
    """
    total_duration: float
    total_distance: float
    bike_distance: float
    walk_distance: float
    number_of_transfers: int | None

class LegUtils():
    """
    Utility class providing static methods for processing and normalizing route
    legs after they are returned by the routing engine.
    """
    # Default route colors based on transport mode
    COLORS = {
        "foot": "blue",
        "bicycle": "red"
    }

    # Default timezone for route time normalization
    TZ = ZoneInfo("Europe/Bratislava")

    @staticmethod
    def process_legs(pattern: TripPattern) -> None:
        """
        Post process a computed trip pattern. The method processes raw legs
        from the routing engine into a final representation.

        Args:
            pattern: Trip pattern containing raw routing legs that will be processed
        """
        legs = pattern.legs

        # Ensure every leg has a display color (used for foot and bicycle segments)
        LegUtils.__assign_default_colors(legs)

        # Extract live vehicle positions for public transport legs
        vehicle_positions = LegUtils.__collect_vehicle_realtime_data(legs)

        # Normalize walking mode representation
        LegUtils.__assign_walk_mode(legs, pattern.modes)

        # Merge consecutive legs belonging to the same service journey
        merged_by_service = LegUtils.__merge_same_service_legs(legs)

        # Insert transfer legs for visualization
        original_legs = LegUtils.__insert_transfer_legs(merged_by_service)

        # Merge time independent legs and compute route statistics
        merged_legs, stats = LegUtils.__compute_accumulated_metrics(merged_by_service)

        # Store final legs and computed information into pattern
        LegUtils.__store_results(pattern, merged_legs, stats, vehicle_positions, original_legs)

    @staticmethod
    def __assign_default_colors(legs: List[Leg]) -> None:
        """
        Assigns default color based on transport mode (used for foot and bicycle segments).

        Args:
            legs: List of legs representing route segments
        """
        for leg in legs:
            # Assign fallback color if none is provided
            if not leg.color:
                leg.color = LegUtils.COLORS.get(leg.mode, "black")

    @staticmethod
    def __collect_vehicle_realtime_data(legs: List[Leg]) -> List[VehicleRealtimeData]:
        """
        Extract vehicles that should be tracked in realtime.

        Args:
            legs: List of legs representing route segments

        Returns:
            List of vehicle realtime data
        """
        vehicle_positions: List[VehicleRealtimeData] = []

        for leg in legs:
            # Track only legs with sufficient data to identify a specific vehicle
            if (
                leg.tripId
                and leg.line
                and leg.otherOptions
                and leg.otherOptions.currentIndex
                and leg.color
                and leg.serviceJourney
                and leg.serviceJourney.passingTimes
            ):
                # Extract the scheduled departure time of the first stop
                time = datetime.strptime(leg.serviceJourney.passingTimes[0]["departure"].time, "%H:%M:%S").time()

                # Combine the leg date with the departure time and attach timezone
                start_time = datetime.combine(leg.aimedStartTime.date(), time, tzinfo=TZ)

                vehicle_positions.append(
                    VehicleRealtimeData(
                        agencyName=leg.line.authority["name"],
                        tripId=leg.tripId,
                        publicCode=leg.line.publicCode,
                        color=leg.color,
                        mode=leg.mode,
                        direction=leg.otherOptions.departures[
                            leg.otherOptions.currentIndex
                        ].direction,
                        startTime=start_time
                    )
                )

        return vehicle_positions

    @staticmethod
    def __assign_walk_mode(legs: List[Leg], modes: List[RoutingMode]) -> None:
        """
        Decides whether a foot segment is actual walking or just a transfer.

        Args:
            legs: List of legs representing the route segments
            modes: List of routing modes used to compute the route
        """
        mode: Mode | Literal[""] = ""
        mode_index = 0

        for leg in legs:
            # Increment waypoint index for consecutive segments
            if mode == leg.mode and mode in TIME_INDEPENDENT_MODES:
                mode_index += 1

            # Mark foot leg as real walking based on routing modes, else the segment is a transfer leg
            if leg.mode == "foot":
                leg.walkMode = (
                    mode_index < len(modes) and (
                        modes[mode_index] == "foot" or 
                        (
                            modes[mode_index] in ["public_bicycle", "bicycle_public"] and
                            leg.distance > 500
                        )
                    )
                )

            mode = leg.mode

    @staticmethod
    def __merge_same_service_legs(legs: List[Leg]) -> List[Leg]:
        """
        Merge consecutive legs that belong to the same transport service.

        Args:
            legs: List of legs representing route segments

        Returns:
            List of legs where consecutive segments belonging to the same
            service are merged into a single leg
        """
        prev_leg = None
        new_legs: List[Leg] = []
        mode: Mode | Literal[""] = ""
        public_code = ""

        for leg in legs:
            leg_public_code = leg.line.publicCode if leg.line else ""

            # Merge legs only if they the ride continues on the same mode and public code
            if (
                prev_leg
                and leg.mode == mode
                and leg_public_code == public_code
                and leg_public_code
            ):
                prev_leg = LegUtils.__merge_legs(prev_leg, leg)
            # Push previous leg when service changes
            else:
                if prev_leg:
                    new_legs.append(prev_leg)
                prev_leg = leg
                public_code = leg_public_code

            # Update last mode
            mode = leg.mode

        # Append final accumulated leg
        if prev_leg:
            new_legs.append(prev_leg)

        return new_legs

    @staticmethod
    def __insert_transfer_legs(legs: List[Leg]) -> List[Leg]:
        """
        Insert transfer legs between public transport segments.

        Args:
            legs: List of processed legs representing route segments

        Returns:
            New list of legs where transfer legs are inserted between
            consecutive public transport segments
        """
        prev_mode: Mode | Literal[""] = ""
        original_legs = deepcopy(legs)
        i = 0

        while i < len(original_legs):
            leg = original_legs[i]

            # Add transfer leg when switching between two segments using public transport
            if (
                prev_mode
                and leg.mode not in ["foot", "bicycle", "wait", "transfer"]
                and prev_mode not in ["foot", "bicycle", "wait", "transfer"]
            ):
                original_legs.insert(i, LegUtils.__prepare_transfer_leg())
                # Skip inserted transfer leg
                i += 1
            
            prev_mode = leg.mode
            i += 1

        return original_legs

    @staticmethod
    def __prepare_transfer_leg() -> Leg:
        """
        Create a placeholder transfer leg.

        Returns:
            Leg representing a transfer segment used mainly for visualization
        """
        return Leg(
            mode="transfer",
            color="gray",
            duration=0,
            pointsOnLink=PointOnLink(
                points=[]
            )
        )

    @staticmethod
    def __compute_accumulated_metrics(
        legs: List[Leg]
    ) -> tuple[List[Leg], _LegStats]:
        """
        Merge compatible legs and compute aggregated route metrics.

        Args:
            legs: List of route legs

        Returns:
            Tuple containing (List of merged legs, _LegStats with aggregated route metrics)
        """
        merged_legs: List[Leg] = []

        duration = 0
        distance = 0
        bike_distance = 0
        walk_distance = 0
        number_of_transfers = None

        # Initialize first active leg
        current = deepcopy(legs[0])

        # Accumulate initial leg distance by mode
        if current.mode == "bicycle":
            bike_distance += current.distance
        if current.mode == "foot":
            walk_distance += current.distance

        for leg in legs[1:]:
            # Accumulate distance by used mode
            if leg.mode == "bicycle":
                bike_distance += leg.distance
            elif leg.mode == "foot":
                walk_distance += leg.distance

            # Merge consecutive time independent legs of the same mode
            if leg.mode == current.mode and leg.mode in TIME_INDEPENDENT_MODES:
                LegUtils.__merge_active_leg(current, leg)
            else:
                # Count number of transfers
                if current.mode not in ["foot", "bicycle", "wait", "transfer"]:
                    number_of_transfers = number_of_transfers + 1 if number_of_transfers else 1

                # Store accumulated duration
                current.accumulatedDuration = duration
                merged_legs.append(current)

                # Update global total duration and distance
                duration += current.duration
                distance += current.distance

                # Leg copy
                current = deepcopy(leg)
        
        # Count final transfer if last leg is public transport
        if current.mode not in TIME_INDEPENDENT_MODES:
            number_of_transfers = number_of_transfers + 1 if number_of_transfers else 1

        # Finalize last leg accumulation
        current.accumulatedDuration = duration
        merged_legs.append(current)

        # Update total duration and distance for final leg
        duration += current.duration
        distance += current.distance

        legs_without_wait: List[Leg] = []
        prev_mode = "foot" # Anything else from bicycle/wait

        for leg in merged_legs:
            # Merge waiting time into adjacent bicycle legs
            if leg.mode == "bicycle" and prev_mode == "wait":
                leg.duration += legs_without_wait[-1].duration
                leg.accumulatedDuration = legs_without_wait[-1].accumulatedDuration
                legs_without_wait[-1] = leg
            elif leg.mode == "wait" and prev_mode == "bicycle":
                legs_without_wait[-1].duration += leg.duration
            else:
                legs_without_wait.append(leg)

            prev_mode = leg.mode

        # Return merged legs and aggregated metrics
        return legs_without_wait, _LegStats(
            duration,
            distance,
            bike_distance,
            walk_distance,
            number_of_transfers
        )
    
    @staticmethod
    def __merge_active_leg(current: Leg, leg: Leg) -> None:
        """
        Merge two consecutive legs of the same time independent mode.

        Args:
            current: The active leg that accumulates the merged data
            leg: The next leg that should be merged into the current leg
        """

        # Extend duration and distance to keep route continuous
        current.duration += leg.duration
        current.distance += leg.distance
        current.aimedEndTime = leg.aimedEndTime

        # Update final destination of merged segment
        current.toPlace = leg.toPlace

        # Create list with the first polyline
        if isinstance(current.pointsOnLink.points, str):
            points = current.pointsOnLink.points
            current.pointsOnLink.points = [points]

        # Append new polyline
        if leg.pointsOnLink:
            points = leg.pointsOnLink.points
            if isinstance(points, str):
                current.pointsOnLink.points.append(points)
            else:
                current.pointsOnLink.points.extend(points)

    @staticmethod
    def __store_results(
        pattern: TripPattern,
        merged_legs: List[Leg],
        stats: _LegStats,
        vehicle_positions: List[VehicleRealtimeData],
        original_legs: List[Leg],
    ) -> None:
        """
        Stores results into trip pattern.

        Args:
            pattern: The trip pattern the results are stored in
            merged_legs: New merged legs to store
            stats: Accumulates stats to store
            vehicle_positions: List of realtime data to store
            original_legs: Original unprocessed legs
        """
        pattern.legs = merged_legs
        pattern.originalLegs = original_legs
        pattern.totalDuration = stats.total_duration
        pattern.totalDistance = stats.total_distance
        pattern.bikeDistance = stats.bike_distance
        pattern.walkDistance = stats.walk_distance
        pattern.vehicleRealtimeData = vehicle_positions
        pattern.totalTime = (
            pattern.aimedEndTime - pattern.legs[0].aimedStartTime   # Total trip time in seconds
        ).total_seconds()

        if stats.number_of_transfers:
            pattern.numOfTransfers = stats.number_of_transfers - 1

    @staticmethod
    def __merge_legs(leg1: Leg, leg2: Leg) -> Leg:
        """
        Merge two consecutive legs into a single leg.
        
        Args:
            leg1: The first leg
            leg2: The second leg

        Returns:
            A new leg representing the merged segment
        """
        merged_service_journey: Optional[ServiceJourney] = None

        service_journey_1 = leg1.serviceJourney
        service_journey_2 = leg2.serviceJourney

        # Merge service journey information if both legs contain it
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

        # Extract geometry points from both legs
        points_1 = leg1.pointsOnLink.points
        points_2 = leg2.pointsOnLink.points

        inactive_points_1 = leg1.pointsOnLink.inactivePoints
        inactive_points_2 = leg2.pointsOnLink.inactivePoints

        merged_points: List[str] = []
        merged_inactive_points: List[str] = []
        
        # Normalize first leg geometry into list form
        if isinstance(points_1, str):
            merged_points.append(points_1)
        else:
            merged_points.extend(points_1)

        # Normalize second leg geometry into list form
        if isinstance(points_2, str):
            merged_points.append(points_2)
        else:
            merged_points.extend(points_2)

        # Normalize first leg geometry into list form
        if isinstance(inactive_points_1, str):
            merged_inactive_points.append(inactive_points_1)
        else:
            merged_inactive_points.extend(inactive_points_1)

        # Normalize second leg geometry into list form
        if isinstance(inactive_points_2, str):
            merged_inactive_points.append(inactive_points_2)
        else:
            merged_inactive_points.extend(inactive_points_2)

        # Create merged leg
        return Leg(
            mode=leg1.mode,
            aimedStartTime=leg1.aimedStartTime,
            aimedEndTime=leg2.aimedEndTime,
            distance=leg1.distance + leg2.distance,
            duration=leg1.duration + leg2.duration,
            pointsOnLink=PointOnLink(
                points=merged_points,
                inactivePoints=merged_inactive_points
            ),
            fromPlace=leg1.fromPlace,
            toPlace=leg2.toPlace,
            color=leg1.color,
            line=leg1.line,
            serviceJourney=merged_service_journey,
            otherOptions=leg1.otherOptions
        )

# End of file leg_utils.py
