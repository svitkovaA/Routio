"""
file: main.py

The main application entry point. Initializes the FastAPI application,
configures CORS and loads required data.
"""

import json
import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from workers import database_worker, gbfs_worker, gtfs_worker, lissy_worker, vehicle_position_worker
from config import BEN_API_KEY, LISSY_API_KEY, LISSY_URL
from services.public_transport_service.lissy import cache_lissy
from services.gtfs_gbfs_service import load_gbfs_data, load_gtfs_data
from routes import geocode, route, status, departures, vehicle_positions
import asyncio
import logging
from database.db import init_pool, close_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Loads and cache data required by the application during startup
    and starts background worker
    """
    # Postgres database connection
    await init_pool()

    # Load General Bike Feed Specification data (bikesharing stations capacities)
    try:
        load_gbfs_data()
    except Exception:
        logging.exception("Initial load_gbfs_data failed")

    # Load General Transit Feed Specification data (public transport schedules for IDS JMK)
    try:
        load_gtfs_data()
    except Exception:
        logging.exception("Initial load_gtfs_data failed")

    # Cache data from Lissy (delays and route shapes)
    try:
        await cache_lissy()
    except Exception:
        logging.exception("Initial cache_lissy failed")

    # Start background worker for data updates
    tasks = [
        asyncio.create_task(vehicle_position_worker()),
        asyncio.create_task(gbfs_worker()),
        asyncio.create_task(gtfs_worker()),
        asyncio.create_task(lissy_worker()),
        asyncio.create_task(database_worker()),
    ]

    yield

    # Close postgres database connection
    await close_pool()

    # Gracefully shut down background workers
    for task in tasks:
        task.cancel()

    for task in tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass

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
app.include_router(vehicle_positions.router)

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
            # "https://walter.fit.vutbr.cz/ben/nextbike/places?from=1768950000000&to=1769537357380",
            # "https://walter.fit.vutbr.cz/ben/nextbike/places?from=1759701600000&to=1759741860000",
            # "https://walter.fit.vutbr.cz/ben/nextbike/places?from=1760047200000&to=1760220000000",
            "https://walter.fit.vutbr.cz/ben/nextbike/records?from=1768950000000&to=1737500400000&station_uid=29078342",
            # "https://walter.fit.vutbr.cz/ben/nextbike/records?from=1737846000000&to=1769537357380&station_uid=27618921",
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
        data = r.json()
        print(json.dumps(data, indent=2))
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

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload=True)

# End of file main.py
