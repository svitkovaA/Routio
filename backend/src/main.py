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
    # Load General Bike Feed Specification data (bikesharing stations capacities)
    load_gbfs_data()

    # Load General Transit Feed Specification data (public transport schedules for JMK CZ)
    load_gtfs_data()

    # Cache data from Lissy
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

# LISSY DELAYS
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
# # LISSY DELAYS END

@app.get("/test")
async def test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            "https://walter.fit.vutbr.cz/ben/nextbike/places?from=1759701600000&to=1859701600000",
            # "https://walter.fit.vutbr.cz/ben/nextbike/records?from=1759701600000&to=1859701600000&station_uid=27618846",
            # "https://walter.fit.vutbr.cz/ben/nextbike/placesAround?from=1759701600000&to=1859701600000&limit=2&position=[49.194872,16.606506]",
            headers={"Authorization": BEN_API_KEY}
        )
        r.raise_for_status()
        return r.json()
    
@app.get("/testWeather")
async def test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            LISSY_URL + "weather/data?from=1759701600000&to=1859701600000",
            headers={"Authorization": LISSY_API_KEY}
        )
        r.raise_for_status()
        return r.json()
    
@app.get("/testWeatherPositions")
async def test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            # LISSY_URL + "weather/positions",
            LISSY_URL + "weather/data?from=1735686000000&to=1767222000000",
            headers={"Authorization": LISSY_API_KEY}
        )
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
