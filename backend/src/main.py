"""
file: main.py

The main application entry point. Initializes the FastAPI application,
configures CORS and loads required data.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from workers import database_worker, gbfs_worker, gtfs_worker, lissy_worker, vehicle_position_worker
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

    # Load General Transit Feed Specification data (public transport schedules for IDS JMK)
    try:
        load_gtfs_data()
    except Exception:
        logging.exception("Initial load_gtfs_data failed")

    # Load General Bike Feed Specification data (bikesharing stations capacities)
    try:
        load_gbfs_data()
    except Exception:
        logging.exception("Initial load_gbfs_data failed")

    # Cache data from Lissy (delays and route shapes)
    try:
        await cache_lissy()
    except Exception:
        logging.exception("Initial cache_lissy failed")

    # Start background workers for data updates
    tasks = [
        asyncio.create_task(gtfs_worker()),
        asyncio.create_task(gbfs_worker()),
        asyncio.create_task(database_worker()),
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
