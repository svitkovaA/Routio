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
    # "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_oc/cs/station_information.json"    # Kahan
}