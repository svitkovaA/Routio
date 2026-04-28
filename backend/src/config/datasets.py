"""
file: datasets.py

Defines dataset sources and local storage paths, includes:
- GTFS and GTFS-RT data
- OSM extract
- GBFS station information feeds
- TIF population data
- OpenWeather data
- District boundaries data
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from typing import List, TypedDict

# Praha + JMK + Olomouc bounds
# NW_LAT = 50.6
# NW_LON = 13.3
# SE_LAT = 48.6
# SE_LON = 17.9

# JMK bounds
NW_LAT = 49.6332550
NW_LON = 15.5424248
SE_LAT = 48.6165408
SE_LON = 17.6469364

# Path to dataset directory
DATASET_DIR = Path("../dataset")

# Local directory for storing GTFS dataset
GTFS_DIR = DATASET_DIR / "gtfs"

IDS_JMK_AGENCY_NAME = "IDS JMK (Data from: KORDIS JMK, DPMB)"

class GTFS_DATASET(TypedDict):
    """
    Class representing one GTFS dataset.
    """
    url: str                # Dataset URL for download
    name: str               # Dataset unique name
    realtime: str | None    # Optional realtime data URL

# GTFS datasets
GTFS_DATASETS: List[GTFS_DATASET] = [
    {
        "url": "https://kordis-jmk.cz/gtfs/gtfs.zip",
        "name": "IDS JMK",
        "realtime": "https://kordis-jmk.cz/gtfs/gtfsReal.dat"
    },
    # {
    #     "url": "https://data.pid.cz/PID_GTFS.zip",
    #     "name": "PID",
    #     "realtime": "https://api.golemio.cz/v2/vehiclepositions/gtfsrt/vehicle_positions.pb"
    # },
    # {
    #     "url": "https://www.dpmo.cz/doc/dpmo-olomouc-cz.zip",
    #     "name": "Olomouc",
    #     "realtime": None
    # },
]

# Download URL for OSM PBF extract for Czech Republic 
OSM_PBF_URL = "https://download.geofabrik.de/europe/czech-republic-latest.osm.pbf"

# Local storage path for OSM PBF file
OSM_PBF_PATH = DATASET_DIR / "osm/czech-republic-latest.osm.pbf"

# Local storage path for Lissy historical delays
LISSY_DELAY_CACHE_PATH = DATASET_DIR / "lissy_cache"

# GBFS datasets
GBFS_URLS = {
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_te/gbfs.json",   # Brno
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_nh/gbfs.json",   # Hodonin
    # # PRAHA
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_tg/gbfs.json",   # Praha
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_tq/gbfs.json",   # Mladoboleslavsko
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_td/gbfs.json",   # Berounsko
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_ni/gbfs.json",   # Kolin
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_co/gbfs.json",   # Benesov
    # # OLOMOUC
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_ti/gbfs.json",   # Olomouc
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_lb/gbfs.json",   # Lipnik nad Becvou
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_nr/gbfs.json"    # Prerov
}

# Directory where population density dataset is stored
POPULATION_DIR = DATASET_DIR / "pop_density"

# Path to the population density raster file
POPULATION_PATH = POPULATION_DIR / "JRC-ESTAT_Census_Population_2021_100m.tif"

# URL used to download the population density dataset
POPULATION_URL = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/MAPS/JRC-ESTAT_Census_Population_2021_100m/JRC-ESTAT_Census_Population_2021_100m.zip"

# URL for the current weather data
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# URL for downloading district bounds
DISTRICT_URL = "https://raw.githubusercontent.com/siwekm/czech-geojson/master/okresy.json"

# Directory where district dataset is stored
DISTRICT_DIR = DATASET_DIR / "districts"

# Path to the district JSON file
DISTRICT_PATH = DISTRICT_DIR / "districts.json"

load_dotenv()
WEATHER_API_KEY = os.environ.get("OPEN_WEATHER_API_KEY", "")

# End of file datasets.py
