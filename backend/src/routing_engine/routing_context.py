from gql.client import AsyncClientSession
from models.route_data import RouteData

class RoutingContext:
    def __init__(self, data: RouteData, session: AsyncClientSession):
        self.data = data
        self.session = session

        self.max_bike_distance = (
            data.max_bike_distance if data.use_own_bike 
            else data.max_bikesharing_distance
        )

        self.bike_speed = (
            data.bike_average_speed if data.use_own_bike
            else data.bikesharing_average_speed
        )

        self.bike_lock_time = (
            data.bike_lock_time if data.use_own_bike
            else data.bikesharing_lock_time
        )
