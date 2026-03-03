"""
file: routing_context.py

Defines a shared routing context used across the routing engine.
"""

from gql.client import AsyncClientSession
from models.route_data import RouteData

class RoutingContext:
    """
    Shared context object passed across routing engine components
    """
    def __init__(self, data: RouteData, session: AsyncClientSession):
        """
        Initializes routing context and derives bicycle parameters.

        Args:
            data: Route data containing user preferences
            session: Asynchronous GraphQL client session for API calls
        """
        self.data = data
        self.session = session

        # Determine bicycle parameters based on the chosen bicycle options
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

# End of file routing_context.py
