from typing import List
from models.route_data import LegPreferences
from models.route import RoutingMode, WaypointGroup

class WaypointGrouper():
    @staticmethod
    def group(
        waypoints: List[str],
        pref: List[LegPreferences]
    ) -> List[WaypointGroup]:
        """
        The function splits a sequence of waypoints into consecutive groups
        according to the modes used in trip segments

        Args:
            waypoints: Ordered list of waypoint identifiers
            pref: List of leg preferences corresponding to waypoint legs
        
        Returns:
            tuple (list of waypoint groups, boolean if the bicycle segment was found)
        """  
        groups: List[WaypointGroup] = []
        i = 0

        # Iterates over waypoints pairs
        while i < len(waypoints) - 1:
            # Initialize a new group with the current waypoint pair
            group = [waypoints[i], waypoints[i + 1]]
            
            # Determine routing mode for the current segment
            mode: RoutingMode | None = pref[i].mode if i < len(pref) else None
            j = i

            # Extend group while consecutive segments share the same mode
            while j < len(pref) - 1 and pref[j + 1].mode == mode:
                group.append(waypoints[j + 2])
                j += 1

            # Create and store WaypointGroup object
            groups.append(
                WaypointGroup(
                    group=group,
                    mode=mode
                )
            )

            # Move index to the next unprocessed segment
            i = j + 1

        return groups
