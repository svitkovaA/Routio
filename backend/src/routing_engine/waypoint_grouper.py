"""
file: waypoint_grouper.py

Provides logic for grouping consecutive legs into segments based on the
defined leg preferences.
"""

from typing import List
from models.route_data import LegPreferences
from models.route import RoutingMode, WaypointGroup

class WaypointGrouper():
    """
    Responsible for grouping waypoints into consecutive segments.
    """
    
    @staticmethod
    def group(
        waypoints: List[str],
        pref: List[LegPreferences]
    ) -> List[WaypointGroup]:
        """
        Splits a sequence of waypoints into consecutive groups according to the
        modes defined in leg preferences.

        Args:
            waypoints: Ordered list of waypoint identifiers
            pref: List of leg preferences corresponding to waypoint legs
        
        Returns:
            List of WaypointGroup objects representing grouped segments
        """  
        groups: List[WaypointGroup] = []

        # Main current segment index
        i = 0

        # Iterates over waypoints pairs
        while i < len(waypoints) - 1:
            # Initialize a new group with the current waypoint pair
            group = [waypoints[i], waypoints[i + 1]]
            
            # Determine routing mode for the current segment
            mode: RoutingMode | None = pref[i].mode if i < len(pref) else None

            # Index for extending the group
            j = i

            # Extend group while the next segments share the same mode
            while j < len(pref) - 1 and pref[j + 1].mode == mode:
                group.append(waypoints[j + 2])
                j += 1

            # Store constructed group with its routing mode
            groups.append(
                WaypointGroup(
                    waypoints=group,
                    mode=mode
                )
            )

            # Move main index to the next unprocessed segment
            i = j + 1

        return groups

# End of file waypoint_grouper.py
