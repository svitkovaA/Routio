"""
file: config.py

Configuration file defining:
- External API endpoints,
- URLs for downloading datasets,
- Local dataset storage paths,
- Loading API keys from environment variables.
"""

import os
from dotenv import load_dotenv

# Photon geocoding API used for geocoding (address to coordinates)
PHOTON_URL = "https://photon.komoot.io/api"

# Nominatim geocoding API used for reverse geocoding (coordinates to address)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# OpenTripPlanner API used for multimodal route planning
OTP_URL = "https://walter.fit.vutbr.cz/otp/transmodel/v3"
# OTP_URL = "http://localhost:8080/otp/transmodel/v3"

# Lissy API used to render route shapes and retrieve historical delay data
LISSY_URL = "https://dexter.fit.vutbr.cz/lissy/api/"

# Available shapes endpoint
SHAPES_URL = LISSY_URL + "shapes/getShapes"

# Specific shape geometry endpoint
SHAPE_URL = LISSY_URL + "shapes/getShape"

# Available trips endpoint
DELAY_TRIPS_URL = LISSY_URL + "delayTrips/getAvailableTrips"

# Available routes endpoint
DELAY_ROUTES_URL = LISSY_URL + "delayTrips/getAvailableRoutes"

# Delay data endpoint
DELAY_DATA_URL = LISSY_URL + "delayTrips/getTripData"

# Weather data endpoint
WEATHER_DATA_URL = LISSY_URL + "weather/data"

# Weather positions endpoint
WEATHER_POSITIONS_URL = LISSY_URL + "weather/positions"

# Ben API used for retrieving information about shared-bike stations and available bicycles
BEN_URL = "https://walter.fit.vutbr.cz/ben/nextbike/"

# Shared-bike stations endpoint
BICYCLE_PLACES_URL = BEN_URL + "places"

# Available bicycles information endpoint
BICYCLE_INFO_URL = BEN_URL + "records"

# TODO currently unused
NEXTBIKE_URL = "https://api.nextbike.net/maps/nextbike-live.json?countries=cz"

# GTFS-RealTime data used for current vehicle position visualisation
GTFSRT_URL = "https://kordis-jmk.cz/gtfs/gtfsReal.dat"

# Local directory for storing GTFS dataset
GTFS_PATH = "../datasets/gtfs"

# Static GTFS dataset download URL
GTFS_URL = "https://kordis-jmk.cz/gtfs/gtfs.zip"

# Download URL for OSM PBF extract for Czech Republic 
OSM_PBF_URL = "https://download.geofabrik.de/europe/czech-republic-latest.osm.pbf"

# Local storage path for OSM PBF file
OSM_PBF_PATH = "../datasets/osm/czech-republic-latest.osm.pbf"

# GBFS station information URLS
STATION_INFORMATION_URLS = {
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_te/cs/station_information.json",   # Brno
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_nh/cs/station_information.json",   # Hodonin
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_oc/cs/station_information.json"    # Kahan
}

# Load variables from .env into the environment
load_dotenv()

LISSY_API_KEY = os.environ.get("LISSY_API_KEY", "")
BEN_API_KEY = os.environ.get("BEN_API_KEY", "")

# DB configuration
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_USER = os.getenv("POSTGRES_USER", "andrea")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_DATABASE = os.getenv("POSTGRES_DB", "prediction")

# End of file config.py
