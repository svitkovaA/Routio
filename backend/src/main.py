"""
file: main.py

The main application entry point. Initializes the FastAPI application,
configures CORS and loads required data.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.geocoding import geocode
from api.departures import departures
from api.route import route
from service.gtfs_rt_service import GTFSRTService
from service.gbfs_service import GBFSService
from service.lissy_service import LissyService
from service.gtfs_service import GTFSService
from workers import database_worker, gbfs_worker, gtfs_worker, lissy_worker, vehicle_position_worker
from api import status, vehicle_positions
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

    # TODO run start up tasks with asyncio.gather

    # Load General Transit Feed Specification data (public transport schedules for IDS JMK)
    try:
        # TODO safe create of all cache object
        await GTFSService.get_instance().reload()
    except Exception:
        logging.exception("Initial load_gtfs_data failed")

    # Load General Bike Feed Specification data (bikesharing stations capacities)
    try:
        await GBFSService.get_instance().reload()
    except Exception:
        logging.exception("Initial load_gbfs_data failed")

    # Cache data from Lissy (delays and route shapes)
    try:
        await LissyService.get_instance().reload()
    except Exception:
        logging.exception("Initial cache_lissy failed")

    # Vehicle positions
    try:
        await GTFSRTService.get_instance().reload()
    except Exception:
        logging.exception("Initial gtfs_rt_service failed")

    # Start background workers for data updates
    tasks = [
        asyncio.create_task(gtfs_worker()),
        asyncio.create_task(gbfs_worker()),
        # asyncio.create_task(database_worker()),
        asyncio.create_task(lissy_worker()),
        asyncio.create_task(vehicle_position_worker()),
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

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload=True)

# End of file main.py
