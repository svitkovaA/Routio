import os
from dotenv import load_dotenv

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

# Load variables from .env into the environment
load_dotenv()

LISSY_API_KEY = os.environ.get("LISSY_API_KEY", "")
BEN_API_KEY = os.environ.get("BEN_API_KEY", "")