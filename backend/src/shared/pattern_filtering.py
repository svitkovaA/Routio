from datetime import datetime
from typing import List
from routing_engine.routing_context import RoutingContext
from models.route import TripPattern
from zoneinfo import ZoneInfo

class PatternFiltering():
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
            trip_patterns: List of all found trip patterns
            data: Data object including user preferences

        Returns:
            Sorted and filtered list of the best trip patterns (max 10)
        """
        new_patterns: List[TripPattern] = []

        # TODO bicycle logic from multimodal (same as the foot)

        # The foot segment set in user preferences in multimodal routing or foot selected for unimodal routing
        foot_in_pref = (
            (
                any(
                    lp.mode == "foot" 
                    for lp in self.__ctx.data.leg_preferences
                ) 
            and self.__ctx.data.mode == "multimodal"
            ) or self.__ctx.data.mode == "foot"
        )
        
        # Filter trip patterns based on the user preferences
        for pattern in trip_patterns:
            # Check the maximal number of transfers
            if pattern.numOfTransfers and pattern.numOfTransfers > self.__ctx.data.max_transfers:
                continue

            # Check the maximal walk distance
            if pattern.walkDistance and pattern.walkDistance > self.__ctx.data.max_walk_distance * 1000 + 50:
                # If the foot leg is set by user, set flag the walk distance is too long to the trip pattern 
                if foot_in_pref:
                    pattern.tooLongWalkDistance = True  
                # The trip pattern will not be shown
                else:
                    continue
            # Check the maximal bicycle distance and set the flag for pattern
            if pattern.bikeDistance and pattern.bikeDistance > self.__ctx.max_bike_distance * 1000 + 50:
                pattern.tooLongBikeDistance = True

            new_patterns.append(pattern)

        # Sort trip patterns based on the user preferences, the shortest trip patterns
        if self.__ctx.data.route_preference == "shortest":
            sorted_patterns = sorted(new_patterns, key=lambda tp: tp.totalDistance if tp.totalDistance else float("inf"))
        # Sort trip patterns based on the user preferences, the minimum number of transfers
        elif self.__ctx.data.route_preference == "transfers":
            sorted_patterns = sorted(new_patterns, key=lambda tp: (tp.numOfTransfers is not None, tp.numOfTransfers if tp.numOfTransfers else 0))
        # Sort trip patterns based on the user preferences, the shortest trip patterns, the time preference
        else:
            # The latest possible departure
            if self.__ctx.data.arrive_by:
                sorted_patterns = sorted(new_patterns, key=lambda tp: self.__ensure_aware(tp.legs[0].aimedStartTime), reverse=True)
            # The soonest possible arrival
            else:
                sorted_patterns = sorted(new_patterns, key=lambda tp: self.__ensure_aware(tp.aimedEndTime))
        
        # Return max 10 trip patterns
        return sorted_patterns[:10]

    @staticmethod
    def __ensure_aware(dt: datetime) -> datetime:
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=PatternFiltering.TZ)
        return dt.astimezone(PatternFiltering.TZ)
