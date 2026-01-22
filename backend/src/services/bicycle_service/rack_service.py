from typing import List
import numpy as np
import overpy   # type: ignore[import-untyped]
from scipy.spatial.distance import cosine
from models.types import BikeRackNode
from utils.geo import haversine_distance

async def find_bike_rack(lat: float, lon: float, radius: int = 1000) -> List[BikeRackNode]:
    print("function: find_bike_rack")

    api = overpy.Overpass()
    query = f"""
        [out:json][timeout:25];
        (
        node["amenity"="bicycle_parking"](around:{radius},{lat},{lon});
        );
        out center;
    """
    try:
        result = api.query(query)
    except Exception:
        return []

    racks: List[BikeRackNode] = []

    for node in result.nodes:
        racks.append({
            "distance": haversine_distance(lat, lon, float(node.lat), float(node.lon)) * 1000,
            "place": {
                "latitude": float(node.lat),
                "longitude": float(node.lon),
                "name": "Bike rack",
                "capacity": node.tags.get("capacity", 5),
            },
            "tags": node.tags,
            "score": 0
        })

    return racks

async def optimal_bike_rack_choice(combination: bool, origin: str, destination: str, max_distance: float = 1000) -> List[BikeRackNode]:
    print("function: optimal_bike_rack_choice")
    origin_list = list(map(float, origin.split(',')))
    destination_list = list(map(float, destination.split(',')))
    racks = await find_bike_rack(*destination_list, radius=1000)
    vectorDestinationOrigin = np.asarray(origin_list) - np.asarray(destination_list)

    if combination:
        angleW = 0.6
        distanceW = 0.4
    else:
        angleW = 0.4
        distanceW = 0.6

    scored_racks: List[BikeRackNode] = []

    for rack in racks:    
        vectorDestinationStation = np.asarray([float(rack["place"]["latitude"]), float(rack["place"]["longitude"])]) - np.asarray(destination_list)
        
        if combination and np.dot(vectorDestinationOrigin, vectorDestinationStation) <= 0:
            continue

        angle = 1 - cosine(vectorDestinationOrigin, vectorDestinationStation)
        normalizedAngle = (angle + 1) * 0.5

        score: float = angleW * normalizedAngle + distanceW * (max_distance - rack["distance"]) / max_distance
    
        rack["score"] = score
        scored_racks.append(rack)

    sorted_racks = sorted(scored_racks, key=lambda x: x["score"], reverse=True)
    return sorted_racks[:10]
