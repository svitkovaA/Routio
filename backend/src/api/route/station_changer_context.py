"""
file: station_changer_context.py

Defines context object used by StationChanger.
"""

from models.bike_station_data import BikeStationData

class StationChangerContext():
    """
    Internal helper context for station change process.
    """
    def __init__(self, data: BikeStationData):
        """
        Initializes context for station change operation.

        Args:
            data: Request payload
        """
        # Reference time used to rerouting
        self.time_cursor = (
            data.original_legs[
                data.leg_index + 1
                if data.leg_index < len(data.original_legs)
                else data.leg_index
            ].aimedEndTime
            if data.route_data.arrive_by
            else data.original_legs[
                data.leg_index - 1
                if data.leg_index > 0
                else data.leg_index
            ].aimedStartTime
        )

        # Selected bike station place object
        self.place = data.bike_stations[data.new_index].place

        # Store original request data
        self.data = data

# End of file station_changer_context.py
