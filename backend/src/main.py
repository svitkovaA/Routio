import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from services.public_transport_service.lissy import cache_lissy
from services.gtfs_gbfs_service import load_gbfs_data, load_gtfs_data
from routes import geocode, route, status, departures

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load General Bike Feed Specification data (bikesharing stations capacities)
    load_gbfs_data()

    # Load General Transit Feed Specification data (public transport schedules for JMK CZ)
    load_gtfs_data()

    # Chache data from Lissy
    await cache_lissy()
    yield

app = FastAPI(lifespan=lifespan)

# Add middleware to handle Cross-Origin Resource Sharing allowing requests from any origin
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

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
