"""
file: pattern_filtering.py

Implements filtering and sorting trip patterns produced by the routing engine
according to constraints defined by user.
"""

from datetime import datetime
from typing import List, Literal
from routing_engine.routing_context import RoutingContext
from models.route import TripPattern
from zoneinfo import ZoneInfo

class PatternFiltering():
    """
    Handles filtering and sorting of trip patterns based on user preferences.
    """
    # Default timezone for route time normalization
    TZ = ZoneInfo("Europe/Bratislava")

    def __init__(self, context: RoutingContext):
        self.__ctx = context

    def filter_and_sort(
        self,
        trip_patterns: List[TripPattern]
    ) -> List[TripPattern]:
        """
        Filters and sort found trip patterns based on the user preferences

        Args:
            trip_patterns: List of all found trip patterns from routing engine

        Returns:
            List of sorted and filtered trip patterns (max 10)
        """
        filtered_patterns: List[TripPattern] = []

        # Check whether bicycle mode is explicitly required by user
        bike_in_pref = self.__mode_in_preferences("bicycle")

        # Check whether walking mode is explicitly required by user
        foot_in_pref = self.__mode_in_preferences("foot")
        
        # Apply filtering constraints
        for pattern in trip_patterns:

            # Enforce maximum number of transfer constraint
            if self.__exceeds_transfer_limit(pattern):
                continue

            # Enforce maximum walking distance constraint
            if self.__exceeds_foot_distance(pattern, foot_in_pref):
                continue
            
            # Enforce maximum bicycle distance constraint
            if self.__exceeds_bike_distance(pattern, bike_in_pref):
                continue

            filtered_patterns.append(pattern)

        sorted_patterns = self.__sort_patterns(filtered_patterns)
        
        # Return at most 10 best patterns
        return sorted_patterns[:10]
    
    def __exceeds_transfer_limit(self, pattern: TripPattern) -> bool:
        """
        Check whether pattern exceeds maximum allowed transfers.
        """
        # No transfer information
        if pattern.numOfTransfers is None:
            return False

        # Compare against transfer limit defined by user
        return pattern.numOfTransfers > self.__ctx.data.max_transfers
    
    def __exceeds_bike_distance(self, pattern: TripPattern, bike_in_pref: bool) -> bool:
        """
        Check whether bicycle distance exceeds allowed limit.
        """
        # No bicycle segment
        if pattern.bikeDistance is None:
            return False
        
        limit = self.__ctx.max_bike_distance * 1000 + 50

        # Bicycle distance within limit
        if pattern.bikeDistance <= limit:
            return False
        
        # If bicycle was explicitly requested in preferences, mark but keep pattern
        if bike_in_pref:
            pattern.tooLongBikeDistance = True
            return False
    
        return True
    
    def __exceeds_foot_distance(self, pattern: TripPattern, foot_in_pref: bool) -> bool:
        """
        Check whether walking distance exceeds allowed limit.
        """
        # No walking segment
        if pattern.walkDistance is None:
            return False
        
        limit = self.__ctx.data.max_walk_distance * 1000 + 50

        # Walking distance within limit
        if pattern.walkDistance <= limit:
            return False
        
        # If walking was explicitly requested in preferences, mark but keep pattern
        if foot_in_pref:
            pattern.tooLongWalkDistance = True
            return False
    
        return True

    def __sort_patterns(self, patterns: List[TripPattern]) -> List[TripPattern]:
        """
        Sort trip patterns based on the user preferences.
        """
        preference = self.__ctx.data.route_preference
        # Sort patterns by total distance
        if preference == "shortest":
            return sorted(
                patterns,
                key=lambda tp: tp.totalDistance if tp.totalDistance else float("inf")
            )
        # Sort patterns by number of transfers
        elif preference == "transfers":
            return sorted(
                patterns,
                key=lambda tp: (tp.numOfTransfers is not None, tp.numOfTransfers if tp.numOfTransfers else 0)
            )
        # Sort patterns by time preference
        else:
            # Latest possible departure in arrival mode
            if self.__ctx.data.arrive_by:
                return sorted(
                    patterns,
                    key=lambda tp: self.__ensure_aware(tp.legs[0].aimedStartTime) if tp.legs else datetime.max, reverse=True
                )
            # Latest soonest possible arrival in departure mode
            else:
                return sorted(
                    patterns,
                    key=lambda tp: self.__ensure_aware(tp.aimedEndTime)
                )

    def __mode_in_preferences(self, mode: Literal["bicycle", "foot"]) -> bool:
        """Check whether a specific mode is explicitly included in user preferences."""
        data = self.__ctx.data

        # Match in unimodal routing
        if data.mode == mode:
            return True

        # Check presence in multimodal leg preferences
        if data.mode == "multimodal":
            return any(lp.mode == mode for lp in data.leg_preferences)

        # Mode not requested by user
        return False

    @staticmethod
    def __ensure_aware(dt: datetime) -> datetime:
        # Attach default timezone
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=PatternFiltering.TZ)
        
        # Convert to system timezone
        return dt.astimezone(PatternFiltering.TZ)
    
# End of file pattern_filtering.py
