"""
file: main.py

The main application entry point. Initializes the FastAPI application,
configures CORS and loads required data
"""

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import BEN_API_KEY, LISSY_API_KEY, LISSY_URL
from services.public_transport_service.lissy import cache_lissy
from services.gtfs_gbfs_service import load_gbfs_data, load_gtfs_data
from routes import geocode, route, status, departures

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Loads and cache data required by the application during startup
    """
    # Load General Bike Feed Specification data (bikesharing stations capacities)
    load_gbfs_data()

    # Load General Transit Feed Specification data (public transport schedules for IDS JMK)
    load_gtfs_data()

    # Cache data from Lissy (delays and route shapes)
    await cache_lissy()
    yield

app = FastAPI(lifespan=lifespan)

# Enable Cross-Origin Resource Sharing allowing requests from any origin
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Routers to handle different API endpoint groups
app.include_router(geocode.router)
app.include_router(route.router)
app.include_router(status.router)
app.include_router(departures.router)

# TODO Lissy delays endpoints
@app.get("/lissy/availableDates")
async def get_available_dates():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            LISSY_URL + "delayTrips/availableDates",
            headers={"Authorization": LISSY_API_KEY}
        )
        r.raise_for_status()
        return r.json()

@app.get("/lissy/testRoutes")
async def test_routes():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            LISSY_URL + "delayTrips/getAvailableRoutes",
            headers={"Authorization": LISSY_API_KEY},
            params={"dates": '[["2025-9-8","2025-9-10"]]'}
        )
        r.raise_for_status()
        return r.json()
    
@app.get("/lissy/testTrips")
async def test_trips():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            LISSY_URL + "delayTrips/getAvailableTrips",
            headers={"Authorization": LISSY_API_KEY},
            params={
                "dates": '[["2025-9-8","2025-9-10"]]', 
                "route_id": 32,                         
                "fullStopOrder": True
            }
        )
        r.raise_for_status()
        return r.json()

@app.get("/lissy/tripData")
async def trip_data():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            LISSY_URL + "delayTrips/getTripData",
            headers={"Authorization": LISSY_API_KEY},
            params={
                "dates": '[["2025-9-8","2025-9-10"]]', 
                "trip_id": 227492                      
            }
        )
        r.raise_for_status()
        return r.json()

# TODO BEN and weather testing endpoints
@app.get("/test")
async def test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            "https://walter.fit.vutbr.cz/ben/nextbike/places?from=1759701600000&to=1759741860000",
            # "https://walter.fit.vutbr.cz/ben/nextbike/places?from=1760047200000&to=1760220000000",
            # "https://walter.fit.vutbr.cz/ben/nextbike/records?from=1759701600000&to=1859701600000&station_uid=27618846",
            # "https://walter.fit.vutbr.cz/ben/nextbike/placesAround?from=1759701600000&to=1859701600000&limit=2&position=[49.194872,16.606506]",
            headers={"Authorization": BEN_API_KEY}
        )
        r.raise_for_status()
        return r.json()
    
    
@app.get("/testWeather")
async def test1():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            LISSY_URL + "weather/data?from=1765686000000&to=1767222000000",
            headers={"Authorization": LISSY_API_KEY}
        )
        r.raise_for_status()
        return r.json()
    
@app.get("/testWeatherPositions")
async def test2():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            LISSY_URL + "weather/positions",
            # LISSY_URL + "weather/data?from=1735686000000&to=1767222000000",
            headers={"Authorization": LISSY_API_KEY}
        )
        r.raise_for_status()
        return r.json()

from datetime import datetime
from zoneinfo import ZoneInfo



if __name__ == "__main__":
    dt = datetime(2025, 10, 6, 11, 11, tzinfo=ZoneInfo("Europe/Bratislava"))
    print(int(dt.timestamp() * 1000))

    ts_ms = 1759701600000  # sem daj svoj unix čas v ms
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=ZoneInfo("Europe/Bratislava"))
    print(dt)

    ts_ms = 1759741860000  # sem daj svoj unix čas v ms
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=ZoneInfo("Europe/Bratislava"))
    print(dt)
    uvicorn.run("main:app", port=8000, reload=True)

# End of file main.py
