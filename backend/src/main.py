"""
file: main.py

The main application entry point. Initializes the FastAPI application,
configures CORS middleware, loads initial data and manages background
workers lifecycle.
"""

import uvicorn, asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import status
from api.geocoding import geocode
from api.departures import departures
from api.route import route
from api import vehicle_realtime_data
from database.db import init_pool, close_pool
from service.workers import (
    database_worker,
    gtfs_worker,
    gbfs_worker, 
    lissy_worker,
    load_initial_data,
    gtfs_rt_worker
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initializes database connection pool, loads required data during
    application startup and starts background workers.
    """
    # Initialize PostgreSQL connection pool
    await init_pool()

    # Load required datasets before serving requests
    await load_initial_data()

    # Start background workers for data updates
    tasks = [
        asyncio.create_task(gtfs_worker()),
        asyncio.create_task(gbfs_worker()),
        asyncio.create_task(database_worker()),
        asyncio.create_task(lissy_worker()),
        asyncio.create_task(gtfs_rt_worker()),
    ]

    yield

    # Close database connection
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

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Register API routers
app.include_router(geocode.router)
app.include_router(route.router)
app.include_router(status.router)
app.include_router(departures.router)
app.include_router(vehicle_realtime_data.router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="127.0.0.1", reload=True)

# End of file main.py
