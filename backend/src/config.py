"""
file: config.py

Defines URLs of the external services used by the application
and loads API keys from environment variables
"""

import os
from dotenv import load_dotenv

# Photon geocoding API used for geocoding (address to coordinates)
PHOTON_URL = "https://photon.komoot.io/api"

# Nominatim geocoding API used for reverse geocoding (coordinates to address)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse" 

# OpenTripPlanner API used for multimodal route planning
# OTP_URL = "https://walter.fit.vutbr.cz/otp/transmodel/v3"
OTP_URL = "http://localhost:8080/otp/transmodel/v3"

# Lissy API used to render route shapes and retrieve historical delay data
LISSY_URL = "https://dexter.fit.vutbr.cz/lissy/api/"

# TODO currently unused
NEXTBIKE_URL = "https://api.nextbike.net/maps/nextbike-live.json?countries=cz"

# GTFS-RealTime data used for current vehicle position visualisation
GTFSRT_URL = "https://kordis-jmk.cz/gtfs/gtfsReal.dat"

# GBFS URLs for Brno, Hodonin and Kahan
station_information_urls = {
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_te/cs/station_information.json",   # Brno
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_nh/cs/station_information.json",   # Hodonin
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_oc/cs/station_information.json"    # Kahan
}

# Load variables from .env into the environment
load_dotenv()
LISSY_API_KEY = os.environ.get("LISSY_API_KEY", "")
BEN_API_KEY = os.environ.get("BEN_API_KEY", "")

# End of file config.py
