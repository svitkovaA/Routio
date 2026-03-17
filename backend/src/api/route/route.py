"""
file: route.py

Route API endpoints, including route recalculation after changing bicycle
station and route calculation based on the user preferences.
"""

import time as t
from fastapi import APIRouter
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from api.route.station_changer import StationChanger
from routing_engine.routing_engine import RoutingEngine
from config.external import OTP_URL
from models.route import Results
from models.route_data import RouteData
from models.bike_station_data import BikeStationData

# Router instance for routing endpoints
router = APIRouter()

@router.post("/changeBikeStation")
async def change_bike_station(data: BikeStationData):
    """
    Recalculates a route after changing a bicycle rack/station
    
    Args:
        data: Request payload
    
    Returns:
        Updated trip pattern reflecting modified rack/station and recalculated
        affected segments
    """
    # Initialize OTP GraphQL transport
    transport = AIOHTTPTransport(url=OTP_URL)

    # Create async OTP session
    async with Client(transport=transport) as session:
        station_changer = StationChanger(data, session)

        # Perform route rebuild
        return await station_changer.change_bike_station()

@router.post("/route")
async def get_route(data: RouteData):
    """
    Computes trip patterns based on user input.

    Args:
        data: Routing configuration
    
    Returns:
        Routing results containing computed trip patterns and active flag
    """
    # Start measuring request processing time
    start = t.perf_counter()

    # Initialize OTP GraphQL transport
    transport = AIOHTTPTransport(url=OTP_URL)

    # Create async OTP session with timeout
    async with Client(transport=transport, execute_timeout=20) as session:
        engine = RoutingEngine(data, session)

        # Execute full routing process
        results = Results(
            tripPatterns=await engine.plan_route(),
            active=True
        )

    # Log request processing duration
    end = t.perf_counter()
    print(f"Duration: {end - start:.4f} sec")

    return results

# End of file route.py
