import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from services.public_transport_service.lissy import cache_lissy
from services.gtfs_gbfs_service import get_capacity_information, load_gtfs_data
from routes import geocode, route, status, departures

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_capacity_information()
    load_gtfs_data()
    await cache_lissy()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(geocode.router)
app.include_router(route.router)
app.include_router(status.router)
app.include_router(departures.router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
