"""
file: external.py

Defines external service endpoints used for:
- Geocoding
- Reverse geocoding
- Route planning (OTP)
"""

# Photon geocoding API used for geocoding (address to coordinates)
PHOTON_URL = "https://photon.komoot.io/api"

# Nominatim geocoding API used for reverse geocoding (coordinates to address)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# OpenTripPlanner API used for multimodal route planning
OTP_URL = "https://walter.fit.vutbr.cz/otp/transmodel/v3"
# OTP_URL = "http://localhost:8080/otp/transmodel/v3"

# End of file external.py
