from copy import deepcopy
from datetime import datetime, timedelta
from typing import List
from models.route import TripPattern

class PatternUtils():

    @staticmethod
    def combine(
        partial_patterns: List[TripPattern],
        connecting_patterns: List[List[TripPattern]],
        arrive_by: bool,
        partial_without_pt: bool = False,
        public_bicycle: bool = False
    ) -> List[TripPattern]:
        """
        Combines partial trip patterns with the following connecting patterns

        Args:
            partial_patterns: List of already constructed trip patterns
            connecting_patterns: List of lists containing new patterns corresponding to each partial pattern
            arrive_by: If true, the planning is arrival based, if false, departure based
            partial_without_pt: If true, partial patterns do not contain public transport, therefore time can be adjusted
            public_bicycle: Parameter indicating routing public_bicycle transport

        Returns:
            List of combined trip patterns
        """
        trip_patterns: List[TripPattern] = []

        # Iterates over all pattern pairs
        for partial_pattern, connections in zip(partial_patterns, connecting_patterns):
            # Skip invalid patterns
            if len(connections) == 0:
                continue
            else:
                # For each possible connection pattern corresponding to the current partial pattern, create a combined result
                for connection in connections:
                    combined_pattern = deepcopy(partial_pattern)

                    # Arrival based routing
                    if arrive_by:
                        new_legs = deepcopy(connection.legs)
                        new_modes = deepcopy(connection.modes)

                        # Justify pattern times when public transport is used in first route segment
                        if partial_without_pt:
                            if public_bicycle:
                                # Shift the partial pattern in time so that its start aligns with the end of the connecting pattern
                                PatternUtils.justify_time(combined_pattern, new_legs[-1].aimedEndTime, False)
                            else:
                                # Shift the connecting pattern in time so that its end aligns with the start of the partial pattern
                                PatternUtils.justify_time(
                                    TripPattern(
                                        aimedEndTime=datetime.min,   # Dummy value
                                        legs=new_legs
                                    ),
                                    partial_pattern.legs[0].aimedStartTime,
                                    True
                                )
                        
                        # Attach connection legs before existing partial legs
                        new_legs.extend(deepcopy(combined_pattern.legs))
                        new_modes.extend(deepcopy(combined_pattern.modes))

                        combined_pattern.legs = new_legs
                        combined_pattern.modes = new_modes
                    # Departure based routing
                    else:
                        # Justify pattern times when public transport is used in first route segment
                        if partial_without_pt:
                            PatternUtils.justify_time(combined_pattern, connection.legs[0].aimedStartTime, True)

                        # Attach new legs after partial_pattern legs
                        combined_pattern.legs.extend(connection.legs)
                        combined_pattern.aimedEndTime = connection.aimedEndTime
                        combined_pattern.modes = combined_pattern.modes + connection.modes
                    trip_patterns.append(combined_pattern)
        return trip_patterns

    @staticmethod
    def justify_time(
        pattern: TripPattern,
        time_cursor: datetime,
        arrive_by: bool
    ) -> None:
        """
        Adjust start and end times of all legs in a trip pattern
        based on a target departure or arrival time

        Args:
            pattern: The trip pattern containing legs and aimed times
            time_cursor: Datetime representing the target departure time 
                (if arrive_by=False) or arrival time (if arrive_by=True)
            arrive_by: If True, the provided time time_cursor is treated as the
                arrival time, if false, the provided time is treated as the departure time

        Returns:
            None
        """        
        legs = pattern.legs

        if arrive_by:
            leg_indices = reversed(range(len(legs)))
            pattern.aimedEndTime = time_cursor
        else:
            leg_indices = range(len(legs))

        # Process each leg and update times
        for index in leg_indices:
            leg = legs[index]

            # Shift time according to leg duration
            if arrive_by:
                leg.aimedEndTime = time_cursor
                time_cursor -= timedelta(seconds=legs[index].duration)
                leg.aimedStartTime = time_cursor
            else:
                leg.aimedStartTime = time_cursor
                time_cursor += timedelta(seconds=legs[index].duration)
                leg.aimedEndTime = time_cursor

        # Shift the final aimed end time for departure planning
        if not arrive_by:
            pattern.aimedEndTime = time_cursor
