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
        # Extract only the part of the route affected by the bike station change
        # (prefix for arrive based routing, suffix for departure based routing)
        self.compressed_legs = (
            data.legs[:data.leg_index + 2] 
            if data.route_data.arrive_by 
            else data.legs[data.leg_index - 1:]
        )

        # Reference time used to rerouting
        self.time_cursor = (
            self.compressed_legs[-1].aimedEndTime
            if data.route_data.arrive_by 
            else self.compressed_legs[0].aimedStartTime
        )

        # Selected bike station place object
        self.place = data.bike_stations[data.new_index].place

        # Store original request data
        self.data = data

# End of file station_changer_context.py
