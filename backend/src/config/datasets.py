"""
file: datasets.py

Defines dataset sources and local storage paths, includes:
- GTFS and GTFS-RT data
- OSM extract
- GBFS station information feeds
- TIF population data
"""

from pathlib import Path

# GTFS-RealTime data used for current vehicle position visualisation
GTFSRT_URL = "https://kordis-jmk.cz/gtfs/gtfsReal.dat"

# Local directory for storing GTFS dataset
GTFS_PATH = "../dataset/gtfs"

# Static GTFS dataset download URL
GTFS_URL = "https://kordis-jmk.cz/gtfs/gtfs.zip"

# Download URL for OSM PBF extract for Czech Republic 
OSM_PBF_URL = "https://download.geofabrik.de/europe/czech-republic-latest.osm.pbf"

# Local storage path for OSM PBF file
OSM_PBF_PATH = "../dataset/osm/czech-republic-latest.osm.pbf"

# Local storage path for Lissy historical delays
LISSY_DELAY_CACHE_PATH = "../dataset/lissy_cache"

# GBFS station information URLS
STATION_INFORMATION_URLS = {
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_te/cs/station_information.json",   # Brno
    "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_nh/cs/station_information.json"    # Hodonin
}

# Directory where population density dataset is stored
POPULATION_DIR = Path("../dataset/pop_density")

# Path to the population density raster file
POPULATION_PATH = POPULATION_DIR / "JRC-ESTAT_Census_Population_2021_100m.tif"

# URL used to download the population density dataset
POPULATION_URL = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/MAPS/JRC-ESTAT_Census_Population_2021_100m/JRC-ESTAT_Census_Population_2021_100m.zip"

# End of file datasets.py
