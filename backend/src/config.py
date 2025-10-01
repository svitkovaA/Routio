import os
from dotenv import load_dotenv

PHOTON_URL = "https://photon.komoot.io/api"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse" 
OTP_URL = "https://walter.fit.vutbr.cz/otp/transmodel/v3"
# OTP_URL = "http://localhost:8080/otp/transmodel/v3"
LISSY_URL = "https://dexter.fit.vutbr.cz/lissy/api/"
NEXTBIKE_URL = "https://api.nextbike.net/maps/nextbike-live.json?countries=cz"

load_dotenv()
LISSY_API_KEY = os.environ.get("LISSY_API_KEY", "")