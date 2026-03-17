"""
file: patterns_utils.py

Utilities responsible for combining partial trip patterns with the
corresponding connections and ensuring time connectivity between connected
route segments.
"""

from copy import deepcopy
from datetime import datetime, timedelta
from typing import List
from models.route import TIME_DEPENDENT_MODES, Leg, TripPattern

class PatternUtils():
    """
    Utility class for combining trip patterns and adjusting their timing.
    """
    @staticmethod
    def combine(
        partial_patterns: List[TripPattern],
        connecting_patterns: List[List[TripPattern]],
        arrive_by: bool
    ) -> List[TripPattern]:
        """
        Combine partial patterns with corresponding connecting patterns into
        complete trip patterns.

        Args:
            partial_patterns: List of already constructed trip patterns
            connecting_patterns: List of lists containing new patterns corresponding to each partial pattern
            arrive_by: If true, the planning is arrival based, if false, departure based

        Returns:
            List of combined trip patterns
        """
        trip_patterns: List[TripPattern] = []

        # Iterate through partial patterns and their corresponding connections
        for partial_pattern, connections in zip(partial_patterns, connecting_patterns):
            # Skip partial patterns without valid connections
            if len(connections) == 0:
                continue
            else:
                # Combine each possible connection with the partial pattern
                for connection in connections:
                    combined_pattern = deepcopy(partial_pattern)

                    # Arrival based routing
                    if arrive_by:
                        new_legs = deepcopy(connection.legs)
                        new_modes = deepcopy(connection.modes)

                        # Adjust times when connection segment does not contain public transport
                        if PatternUtils.__legs_without_pt(new_legs):
                            # Align connection end to partial start
                            PatternUtils.justify_time(
                                TripPattern(legs=new_legs),
                                partial_pattern.legs[0].aimedStartTime,
                                True
                            )
                        # Adjust times when partial segment does not contain public transport
                        elif PatternUtils.__legs_without_pt(combined_pattern.legs):
                            # Align partial pattern start to connection end
                            PatternUtils.justify_time(combined_pattern, new_legs[-1].aimedEndTime, False)
                        
                        # Prepend connection before partial segment
                        new_legs.extend(deepcopy(combined_pattern.legs))
                        new_modes.extend(deepcopy(combined_pattern.modes))

                        combined_pattern.legs = new_legs
                        combined_pattern.modes = new_modes

                    # Departure based routing
                    else:
                        # Align partial start to connection start if needed
                        if PatternUtils.__legs_without_pt(combined_pattern.legs):
                            PatternUtils.justify_time(combined_pattern, connection.legs[0].aimedStartTime, True)

                        # Append connection after partial segment
                        combined_pattern.legs.extend(connection.legs)
                        combined_pattern.aimedEndTime = connection.aimedEndTime
                        combined_pattern.modes = combined_pattern.modes + connection.modes
                    
                    # Store combined result
                    trip_patterns.append(combined_pattern)

        return trip_patterns

    @staticmethod
    def __legs_without_pt(legs: List[Leg]) -> bool:
        """
        Checks whether the legs are without public transport.

        Args:
            legs: List of route legs

        Returns:
            True if legs are without public transport, false otherwise
        """
        return not any(leg.mode in TIME_DEPENDENT_MODES for leg in legs)

    @staticmethod
    def justify_time(
        pattern: TripPattern,
        time_cursor: datetime,
        arrive_by: bool
    ) -> None:
        """
        Shift all leg times in a pattern to match a given departure or arrival time.

        Args:
            pattern: The trip pattern containing legs and aimed times
            time_cursor: Datetime representing the target departure time 
                (if arrive_by=False) or arrival time (if arrive_by=True)
            arrive_by: If True, the provided time time_cursor is treated as the
                arrival time, if false, the provided time is treated as the departure time
        """        
        legs = pattern.legs

        # Determine iteration direction based on planning mode
        if arrive_by:
            leg_indices = reversed(range(len(legs)))
            # Set final arrival time
            pattern.aimedEndTime = time_cursor
        else:
            leg_indices = range(len(legs))

        # Adjust each leg sequentially
        for index in leg_indices:
            leg = legs[index]

            # Shift time according to leg duration
            if arrive_by:
                # Set arrival time
                leg.aimedEndTime = time_cursor

                # Move backward in time
                time_cursor -= timedelta(seconds=legs[index].duration)

                # Set departure time
                leg.aimedStartTime = time_cursor
            else:
                # Set departure time
                leg.aimedStartTime = time_cursor

                # Move forward in time
                time_cursor += timedelta(seconds=legs[index].duration)

                # Set arrival time
                leg.aimedEndTime = time_cursor

        # Update pattern end time for departure based planning
        if not arrive_by:
            pattern.aimedEndTime = time_cursor

# End of file pattern_utils.py
