import os
from dotenv import load_dotenv

# External service URLs

# Photon geocoding API used for forward geocoding (address to coordinates)
PHOTON_URL = "https://photon.komoot.io/api"

# Nominatim geocoding API used for reverse geocoding (coordinates to address)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse" 

# OpenTripPlanner API used for multimodal route planning
# OTP_URL = "https://walter.fit.vutbr.cz/otp/transmodel/v3"
OTP_URL = "http://localhost:8080/otp/transmodel/v3"

# Lissy API used to render route shapes and retrieve historical delay data
LISSY_URL = "https://dexter.fit.vutbr.cz/lissy/api/"

# TODO nepouziva sa
NEXTBIKE_URL = "https://api.nextbike.net/maps/nextbike-live.json?countries=cz"

# Load ariables from .env into the environment
load_dotenv()
LISSY_API_KEY = os.environ.get("LISSY_API_KEY", "")