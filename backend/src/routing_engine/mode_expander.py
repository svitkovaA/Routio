"""
file: mode_expander.py

Implements multimodal expansion logic for routing.
"""

from itertools import product
from typing import List
from models.route_data import LegPreferences
from models.route import RoutingMode, WaypointGroup
from routing_engine.routing_context import RoutingContext
from routing_engine.waypoint_grouper import WaypointGrouper
from shared.geo_math import GeoMath

class ModeExpander():
    """
    Expands multimodal waypoint groups into concrete routing mode combinations.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes multimodal expander with routing context.

        Args:
            context: Shared RoutingContext with route configuration
        """
        self.__ctx = context

        # Detects if bicycle was explicitly requested in preferences
        self.__contains_bike = any(
            preference.mode == "bicycle" 
            for preference in self.__ctx.data.leg_preferences
        )

        # Precompute borderline distance where bike becomes faster than walking
        self.__borderline_distance = self.__get___borderline_distance()
    
    def expand_multimodal_group(
        self, 
        group: WaypointGroup, 
        is_first_segment: bool,
        was_bike_used: bool
    ) -> List[List[WaypointGroup]]:
        """
        Expands a multimodal group into all possible transport mode combinations

        Args:
            group: Multimodal waypoint group
            is_first_segment: Indicates, whether this is the first segment of the route
            was_bike_used: Indicates, whether bicycle has already been used earlier

        Returns:
            List of possible grouped waypoint sequences
        """
        # Stores possible transport modes per segment
        possible_modes: List[List[RoutingMode]] = []

        # Computes group distance
        total_distance = self.__total_distance_km(group.waypoints)

        i = 0
        while i + 1 < len(group.waypoints):
            # Initialize possible modes list for this segment
            possible_modes.append([])
            
            # Compute distance between two consecutive waypoints
            distance = GeoMath.haversine_distance_km(
                *map(float, group.waypoints[i].split(',')), 
                *map(float, group.waypoints[i + 1].split(','))
            )
            
            # Allow walking within threshold
            if distance * 1.2 <= self.__ctx.data.max_walk_distance:
                possible_modes[i].append("foot")
            
            # Allow public transport for medium/long distances
            if distance >= 0.5:
                possible_modes[i].append("walk_transit")
            
            # Bicycle in general allowed only if not already used and own bicycle allowed only on first route segment
            if (
                not self.__contains_bike and
                not was_bike_used and
                (is_first_segment or not self.__ctx.data.use_own_bike)
            ):
                # Allow direct bicycle segment
                if self.__borderline_distance <= distance and distance * 1.2 <= self.__ctx.max_bike_distance:
                    possible_modes[i].append("bicycle")
                
                # Allow Combination modes bicycle_public and public_bicycle if distance is too long for bicycle
                if total_distance * 1.2 > self.__ctx.max_bike_distance:
                    possible_modes[i].append("bicycle_public")

                    # Add reverse combination, public_bicycle, considered just for shared bicycle
                    if not self.__ctx.data.use_own_bike:
                        possible_modes[i].append("public_bicycle")

            # After first iteration, segment is no longer first
            is_first_segment = False        
            i += 1

        # Cartesian product of all segment mode possibilities
        possible_mode_combinations = list(product(*possible_modes))

        possible_groups: List[List[WaypointGroup]] = []

        # Convert each mode combination into grouped segments
        for combination in possible_mode_combinations:
            groups = WaypointGrouper.group(
                group.waypoints,
                [
                    LegPreferences(
                        mode=mode,
                        wait=0
                    )
                    for mode in combination
                ]
            )

            # Keep only logically valid combinations
            if self.__is_valid_group_sequence(groups):
                possible_groups.append(groups)
        
        # Reverse group order if planning on arrival
        if self.__ctx.data.arrive_by:
            for i in range(len(possible_groups)):
                possible_groups[i] = list(reversed(possible_groups[i]))
                
        return possible_groups

    def __get___borderline_distance(self) -> float:
        """
        Computes distance where bicycle becomes faster than walking.

        Returns:
            Distance threshold in kilometers
        """
        # If bicycle is slower than walking, never prefer it
        if self.__ctx.bike_speed <= self.__ctx.data.walk_speed:
            return float("inf")
        
        # Convert lock/unlock time to hours
        bike_lock_time_hours = self.__ctx.bike_lock_time / 60
        bike_walk_distance = 0.25

        # Shared bicycles require double locking time and walking distance
        if not self.__ctx.data.use_own_bike:
            bike_lock_time_hours *= 2
            bike_walk_distance *= 2

        # Compute distance where bike becomes faster than walking
        distance = bike_walk_distance + (
            (bike_lock_time_hours) / 
            (1 / self.__ctx.data.walk_speed - 1 / self.__ctx.bike_speed)
        )
        
        return distance
    
    @staticmethod
    def __is_valid_group_sequence(groups: List[WaypointGroup]) -> bool:
        """
        Validates logical correctness of a sequence of waypoint groups.

        Returns:
            True, if the group sequence is logically valid, false otherwise
        """
        # Count bicycle segments
        bike_count = sum(
            group.mode in ["bicycle", "bicycle_public", "public_bicycle"] 
            for group in groups
        )
        
        # Allow at most one bicycle segment
        if bike_count >= 2:
            return False
    
        # Filter logically invalid consecutive combinations
        if (ModeExpander.__contains_mode_sequence(groups, ["bicycle_public", "walk_transit"]) or 
            ModeExpander.__contains_mode_sequence(groups, ["walk_transit", "public_bicycle"])):
            return False
        
        return True

    @staticmethod
    def __contains_mode_sequence(
        group: List[WaypointGroup],
        mode_sequence: List[str]
    ) -> bool:
        """
        Check whether a list of waypoint groups contains a given contiguous 
        subsequence of transport modes.

        Args:
            group: List of waypoint groups
            mode_sequence: List of transport modes

        Returns:
            True if the subsequence of modes is present, false otherwise
        """
        # Iterates over the list with the sliding window
        for i in range(len(group) - len(mode_sequence) + 1):

            # Compare modes of the current window with the target mode sequence
            if [group.mode for group in group[i:i+len(mode_sequence)]] == mode_sequence:
                return True
        
        return False

    @staticmethod
    def __total_distance_km(waypoints: List[str]) -> float:
        """
        Computes total distance between consecutive waypoints.

        Args:
            waypoints: The waypoints the distance should be computed between
        
        Returns:
            Total distance in kilometers
        """
        total_distance = 0
        i = 0

        # Sum distances between consecutive waypoints
        while i + 1 < len(waypoints):
            total_distance += GeoMath.haversine_distance_km(
                *map(float, waypoints[i].split(',')), 
                *map(float, waypoints[i + 1].split(','))
            )
            i += 1
        
        return total_distance

# End of file mode_expander.py
