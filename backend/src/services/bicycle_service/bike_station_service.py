from services.otp_service import nearest_bike_stations
from services.gtfs_gbfs_service import bike_station_capacities
import numpy as np
from scipy.spatial.distance import cosine

async def optimal_origin_bike_station_choice(origin: tuple[float, float], destination: tuple[float, float], max_distance: float, combination: bool, use_semicircle: bool, session):
    print("function: optimal_bike_rack_choice")
    nodes = await nearest_bike_stations(*origin, session, max_distance)
    vectorOriginDestination = np.array(destination) - np.array(origin)
    if combination:
        angleW=0.4
        bikesAvailableW = 0.3
        distanceW = 0.3
    else:
        angleW = 0.1
        bikesAvailableW = 0.4
        distanceW = 0.5

    scoredNodes = []

    trashed_nodes = []
    for node in nodes:
        in_semicircle = True
        node = node["node"]
        if not node["place"].get("bikesAvailable") or node["place"]["bikesAvailable"] == 0:
            continue

        vectorOriginStation = np.array([node["place"]["latitude"], node["place"]["longitude"]]) - np.array(origin)
        if use_semicircle and combination and np.dot(vectorOriginDestination, vectorOriginStation) <= 0:
            in_semicircle = False

        angle = 1 - cosine(vectorOriginDestination, vectorOriginStation)
        normalizedAngle = (angle + 1) * 0.5

        score: float = angleW * normalizedAngle + bikesAvailableW * np.clip(node["place"]["bikesAvailable"], 0, 5) * 0.2 + distanceW * (max_distance - node["distance"]) / max_distance
    
        node["score"] = score
        if not in_semicircle:
            trashed_nodes.append(node)
        else:
            scoredNodes.append(node)

    if len(scoredNodes) == 0:
        scoredNodes = trashed_nodes

    sortedNodes = sorted(scoredNodes, key=lambda x: x["score"], reverse=True)
    return sortedNodes[:10]
    
async def optimal_destination_bike_station_choice(origin: tuple[float, float], destination: tuple[float, float], max_distance: float, combination: bool, use_semicircle: bool, session): 
    print("function: optimal_destination_bike_station_choice")
    nodes = await nearest_bike_stations(*destination, session, max_distance)
    vectorDestinationOrigin = np.array(origin) - np.array(destination)

    if combination:
        angleW = 0.4
        spacesAvailableW = 0.3
        distanceW = 0.3
    else:
        angleW = 0.3
        spacesAvailableW = 0.3
        distanceW = 0.4

    scoredNodes = []

    trashed_nodes = []
    for node in nodes:
        in_semicircle = True
        node = node["node"]
        spacesAvailable = 1
        id = node["place"].get("id")
        if not id:
            continue
        capacity = bike_station_capacities[id]
        if capacity is not None:
            spacesAvailable = (capacity - node["place"]["bikesAvailable"]) / capacity

        if spacesAvailable == 0:
            continue
        
        vectorDestinationStation = np.array([node["place"]["latitude"], node["place"]["longitude"]]) - np.array(destination)
        
        if use_semicircle and combination and np.dot(vectorDestinationOrigin, vectorDestinationStation) <= 0:
            in_semicircle = False

        angle = 1 - cosine(vectorDestinationOrigin, vectorDestinationStation)
        normalizedAngle = (angle + 1) * 0.5

        score: float = angleW * normalizedAngle + spacesAvailableW * spacesAvailable + distanceW * (max_distance - node["distance"]) / max_distance
    
        node["score"] = score
        if not in_semicircle:
            trashed_nodes.append(node)
        else:
            scoredNodes.append(node)

    if len(scoredNodes) == 0:
        scoredNodes = trashed_nodes

    sortedNodes = sorted(scoredNodes, key=lambda x: x["score"], reverse=True)
    return sortedNodes[:10]
