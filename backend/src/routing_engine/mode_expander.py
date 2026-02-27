from itertools import product
from typing import List
from models.route_data import LegPreferences
from models.route import RoutingMode, WaypointGroup
from routing_engine.routing_context import RoutingContext
from routing_engine.waypoint_grouper import WaypointGrouper
from shared.geo_math import GeoMath

class ModeExpander():
    def __init__(self, context: RoutingContext):
        self.__ctx = context
        self.__contains_bike = any(
            preference.mode == "bicycle" 
            for preference in self.__ctx.data.leg_preferences
        )
        self.__borderline_distance = self.__get___borderline_distance()
    
    def expand_multimodal_group(
        self, 
        group: WaypointGroup, 
        is_first_segment: bool,
        was_bike_used: bool
    ) -> List[List[WaypointGroup]]:
        # Stores possible transport modes per segment
        possible_modes: List[List[RoutingMode]] = []

        # Total group distance
        total_distance = self.__total_distance_km(group.group)

        i = 0
        while i + 1 < len(group.group):
            # Create empty list of modes for current segment
            possible_modes.append([])
            
            # Compute distance between two consecutive waypoints
            distance = GeoMath.haversine_distance_km(
                *map(float, group.group[i].split(',')), 
                *map(float, group.group[i + 1].split(','))
            )
            
            # Allow walking if distance within max walk threshold
            if distance * 1.2 <= self.__ctx.data.max_walk_distance:
                possible_modes[i].append("foot")
            
            # Allow public transport for medium/long distances
            if distance >= 0.5:
                possible_modes[i].append("walk_transit")
            
            # Bicycle allowed only if not already used and own bicycle only on first route segment
            if not self.__contains_bike and not was_bike_used and (is_first_segment or not self.__ctx.data.use_own_bike):

                # Bicycle segment
                if self.__borderline_distance <= distance and distance * 1.2 <= self.__ctx.max_bike_distance:
                    possible_modes[i].append("bicycle")
                
                # Combination modes bicycle_public and public_bicycle if distance is too long for bicycle
                if total_distance * 1.2 > self.__ctx.max_bike_distance:
                    possible_modes[i].append("bicycle_public")

                    # Add reverse combination, public_bicycle, just for shared bicycle
                    if not self.__ctx.data.use_own_bike:
                        possible_modes[i].append("public_bicycle")

            # After first iteration, segment is no longer first
            is_first_segment = False        
            i += 1

        # Make Cartesian product of all segment mode possibilities
        possible_mode_combinations = list(product(*possible_modes))

        possible_groups: List[List[WaypointGroup]] = []

        # Convert mode combination into grouped waypoint segments
        for combination in possible_mode_combinations:
            groups = WaypointGrouper.group(
                group.group,
                [
                    LegPreferences(
                        mode=mode,
                        wait=0
                    )
                    for mode in combination
                ]
            )

            # Keep only logically valid group combinations
            if self.__is_valid_group_sequence(groups):
                possible_groups.append(groups)
        
        # Reverse conditionally to plan from the end of the route
        if self.__ctx.data.arrive_by:
            for i in range(len(possible_groups)):
                possible_groups[i] = list(reversed(possible_groups[i]))
                
        return possible_groups

    def __get___borderline_distance(self) -> float:
        # If bicycle is slower than walking, bicycle is newer faster option
        if self.__ctx.bike_speed <= self.__ctx.data.walk_speed:
            return float("inf")
        
        # Convert lock/unlock time to hours
        bike_lock_time_hours = self.__ctx.bike_lock_time / 60
        bike_walk_distance = 0.25

        # # Shared bicycles require locking twice and the distance is usually longer
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
        subsequence of transport modes

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
