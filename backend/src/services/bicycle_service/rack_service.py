"""
file: bike_station_service.py

Implements PostGIS based rack discovery and a scoring model
for selecting optimal bicycle rack near the destination.
"""

from typing import List
import numpy as np
from scipy.spatial.distance import cosine
from database.db import create_conn
from models.route import BikeRackNode, BikeRackPlace, RackRow

# TODO unused function
# import overpy   # type: ignore[import-untyped]
# from utils.geo import haversine_distance_km
# async def find_bike_rack(lat: float, lon: float, radius: int = 1000) -> List[BikeRackNode]:
#     """
#     Find bicycle parking racks near a given geographic location

#     Args:
#         lat: Latitude of the search center
#         lon: Longitude of the search center
#         radius: Search radius in meters

#     Returns:
#         List of nearby bicycle racks
#     """
#     print("function: find_bike_rack")

#     api = overpy.Overpass()

#     # Overpass query for bicycle parking nodes within a radius
#     query = f"""
#         [out:json][timeout:25];
#         (
#         node["amenity"="bicycle_parking"](around:{radius},{lat},{lon});
#         );
#         out center;
#     """
#     try:
#         result = api.query(query)
#     except Exception:
#         return []

#     racks: List[BikeRackNode] = []

#     for node in result.nodes:
#         racks.append({
#             # Distance from input location in meters
#             "distance": haversine_distance_km(lat, lon, float(node.lat), float(node.lon)) * 1000,
#             "place": {
#                 "latitude": float(node.lat),
#                 "longitude": float(node.lon),
#                 "name": "Bike rack",
#                 # Default capacity is used if not specified in OSM tags
#                 "capacity": node.tags.get("capacity", 5),
#             },
#             "score": 0
#         })

#     return racks

async def find_bike_rack(lat: float, lon: float, radius: int = 1000) -> List[BikeRackNode]:
    """
    Find bicycle parking racks near a given geographic location

    Args:
        lat: Latitude of the search center
        lon: Longitude of the search center
        radius: Search radius in meters

    Returns:
        List of nearby bicycle racks
    """
    print("function: find_bike_rack")

    query = """
        SELECT
            osm_id,
            lat,
            lon,
            capacity,
            ST_Distance(
                geom::geography,
                ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
            ) AS distance
        FROM bicycle_racks
        WHERE ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
            $3
        )
        ORDER BY distance;
    """

    async with create_conn() as conn:                       # type: ignore
        rows = await conn.fetch(query, lon, lat, radius)    # type: ignore

    racks: List[BikeRackNode] = []

    for raw_row in rows:    # type: ignore
        try:
            row = RackRow.model_validate(dict(raw_row))
        except:
            continue

        racks.append(
            BikeRackNode(
                distance=row.distance,
                place=BikeRackPlace(
                    latitude=row.lat,
                    longitude=row.lon,
                    name="Bike rack",
                    capacity=row.capacity if row.capacity is not None else 5
                )
            )
        )

    return racks

async def optimal_bike_rack_choice(
    combination: bool, 
    origin: str, 
    destination: str, 
    max_distance: float = 1000
) -> List[BikeRackNode]:
    """
    Select optimal bicycle parking racks based on direction and distance

    Args:
        combination:
        origin: Origin coordinates in format lat,lon
        destination: Destination coordinates in format lat,lon
        max_distance:

    Returns:
        
    """
    print("function: optimal_bike_rack_choice")

    # Parse coordinate strings
    origin_list = list(map(float, origin.split(',')))
    destination_list = list(map(float, destination.split(',')))

    # Find bicycle racks near the destination
    racks = await find_bike_rack(*destination_list, radius=1000)

    # Vector representing travel direction
    vectorDestinationOrigin = np.asarray(origin_list) - np.asarray(destination_list)

    # Weight configuration
    if combination:
        angleW = 0.6
        distanceW = 0.4
    else:
        angleW = 0.4
        distanceW = 0.6

    scored_racks: List[BikeRackNode] = []

    # Iterate over all racks
    for rack in racks:  
        # Vector from destination to bicycle rack  
        vectorDestinationStation = np.asarray([
            rack.place.latitude, 
            rack.place.longitude
        ]) - np.asarray(destination_list)
        
        # Skip racks in the opposite direction of travel
        if combination and np.dot(vectorDestinationOrigin, vectorDestinationStation) <= 0:
            continue

        # Compute normalized similarity in range <0,1>
        angle = 1 - cosine(vectorDestinationOrigin, vectorDestinationStation)
        normalizedAngle = (angle + 1) * 0.5

        # Final rack score combining direction and distance
        rack.score = angleW * normalizedAngle + distanceW * (max_distance - rack.distance) / max_distance
    
        scored_racks.append(rack)

    # Sort racks by score and return top results
    sorted_racks = sorted(scored_racks, key=lambda x: x.score, reverse=True)

    return sorted_racks[:10]

# End of file rack_service.py
