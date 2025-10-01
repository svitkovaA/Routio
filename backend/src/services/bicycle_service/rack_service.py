import numpy as np
import overpy
from scipy.spatial.distance import cosine
from utils.geo import haversine_distance

async def find_bike_rack(lat: float, lon: float, radius: int = 1000):
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

    racks = []

    for node in result.nodes:
        racks.append({
            "distance": haversine_distance(lat, lon, float(node.lat), float(node.lon)) * 1000,
            "place": {
                "latitude": float(node.lat),
                "longitude": float(node.lon),
                "name": "Bike rack",
                "capacity": node.tags.get("capacity", 5),
            },
            "tags": node.tags
        })

    return racks

async def optimal_bike_rack_choice(combination: bool, origin: str, destination: str, max_distance: float = 1000):
    print("function: optimal_bike_rack_choice")
    origin = list(map(float, origin.split(',')))
    destination = list(map(float, destination.split(',')))
    racks = await find_bike_rack(*destination)
    vectorDestinationOrigin = np.array(origin) - np.array(destination)

    if combination:
        angleW = 0.6
        distanceW = 0.4
    else:
        angleW = 0.4
        distanceW = 0.6

    scored_racks = []

    for rack in racks:    
        vectorDestinationStation = np.array([float(rack["place"]["latitude"]), float(rack["place"]["longitude"])]) - np.array(destination)
        
        if combination and np.dot(vectorDestinationOrigin, vectorDestinationStation) <= 0:
            continue

        angle = 1 - cosine(vectorDestinationOrigin, vectorDestinationStation)
        normalizedAngle = (angle + 1) * 0.5

        score: float = angleW * normalizedAngle + distanceW * (max_distance - rack["distance"]) / max_distance
    
        rack["score"] = score
        scored_racks.append(rack)

    sorted_racks = sorted(scored_racks, key=lambda x: x["score"], reverse=True)
    return sorted_racks[:10]
