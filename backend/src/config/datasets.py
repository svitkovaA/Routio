"""
file: datasets.py

Defines dataset sources and local storage paths, includes:
- GTFS and GTFS-RT data
- OSM extract
- GBFS station information feeds
- TIF population data
"""

from pathlib import Path
from typing import List, TypedDict

# Praha + JMK + Olomouc
# NW_LAT = 50.6
# NW_LON = 13.3
# SE_LAT = 48.6
# SE_LON = 17.9

# JMK
NW_LAT = 49.6332550
NW_LON = 15.5424248
SE_LAT = 48.6165408
SE_LON = 17.6469364

# Local directory for storing GTFS dataset
GTFS_DIR = Path("../dataset/gtfs")

IDS_JMK_AGENCY_NAME = "IDS JMK (Data from: KORDIS JMK, DPMB)"

class GTFS_DATASET(TypedDict):
    url: str
    name: str
    realtime: str | None

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
OSM_PBF_PATH = "../dataset/osm/czech-republic-latest.osm.pbf"

# Local storage path for Lissy historical delays
LISSY_DELAY_CACHE_PATH = "../dataset/lissy_cache"

# GBFS station information URLS
STATION_INFORMATION_URLS = {
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_te/cs/station_information.json",   # Brno
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_nh/cs/station_information.json",   # Hodonin
    # PRAHA
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_tg/cs/station_information.json",   # Praha
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_tq/cs/station_information.json",   # Mladoboleslavsko
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_td/cs/station_information.json",   # Berounsko
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_ni/cs/station_information.json",   # Kolin
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_co/cs/station_information.json",   # Benesov
    # # OLOMOUC
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_ti/cs/station_information.json",   # Olomouc
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_lb/cs/station_information.json",   # Lipnik nad Becvou
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_nr/cs/station_information.json"    # Prerov
}

# Directory where population density dataset is stored
POPULATION_DIR = Path("../dataset/pop_density")

# Path to the population density raster file
POPULATION_PATH = POPULATION_DIR / "JRC-ESTAT_Census_Population_2021_100m.tif"

# URL used to download the population density dataset
POPULATION_URL = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/MAPS/JRC-ESTAT_Census_Population_2021_100m/JRC-ESTAT_Census_Population_2021_100m.zip"

# End of file datasets.py
