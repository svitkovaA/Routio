from typing import List, Tuple
from models.types import BikeStationNode
from services.otp_service import nearest_bike_stations
from services.gtfs_gbfs_service import bike_station_capacities
import numpy as np
from scipy.spatial.distance import cosine
from gql.client import AsyncClientSession

async def optimal_origin_bike_station_choice(
    origin: Tuple[float, float], 
    destination: Tuple[float, float], 
    max_distance: int, 
    combination: bool, 
    use_semicircle: bool, 
    session: AsyncClientSession
) -> List[BikeStationNode]:
    print("function: optimal_bike_rack_choice")
    nodes = await nearest_bike_stations(*origin, session, max_distance)
    vectorOriginDestination = np.asarray(destination, dtype=np.float64) - np.asarray(origin, dtype=np.float64)
    if combination:
        angleW = 0.4
        bikesAvailableW = 0.3
        distanceW = 0.3
    else:
        angleW = 0.1
        bikesAvailableW = 0.4
        distanceW = 0.5

    scoredNodes: List[BikeStationNode] = []
    trashed_nodes: List[BikeStationNode] = []
    for node in nodes:
        in_semicircle = True
        node = node["node"]
        if node["place"].get("bikesAvailable", 0) == 0:
            continue

        vectorOriginStation = np.asarray([node["place"]["latitude"], node["place"]["longitude"]], dtype=np.float64) - np.asarray(origin, dtype=np.float64)
        if use_semicircle and combination and np.dot(vectorOriginDestination, vectorOriginStation) <= 0:
            in_semicircle = False

        angle = 1 - cosine(vectorOriginDestination, vectorOriginStation)
        normalizedAngle = (angle + 1) * 0.5

        score: float = angleW * normalizedAngle + bikesAvailableW * np.clip(node["place"].get("bikesAvailable", 0), 0, 5) * 0.2 + distanceW * (max_distance - node["distance"]) / max_distance
    
        node["score"] = score
        if not in_semicircle:
            trashed_nodes.append(node)
        else:
            scoredNodes.append(node)

    if len(scoredNodes) == 0:
        scoredNodes = trashed_nodes

    sortedNodes = sorted(scoredNodes, key=lambda x: x["score"], reverse=True)
    return sortedNodes[:10]
    
async def optimal_destination_bike_station_choice(
    origin: tuple[float, float], 
    destination: tuple[float, float],
    max_distance: int, 
    combination: bool, 
    use_semicircle: bool, 
    session: AsyncClientSession
) -> List[BikeStationNode]: 
    print("function: optimal_destination_bike_station_choice")
    nodes = await nearest_bike_stations(*destination, session, max_distance)
    vectorDestinationOrigin = np.asarray(origin) - np.asarray(destination)

    if combination:
        angleW = 0.4
        spacesAvailableW = 0.3
        distanceW = 0.3
    else:
        angleW = 0.3
        spacesAvailableW = 0.3
        distanceW = 0.4

    scoredNodes: List[BikeStationNode] = []
    trashed_nodes: List[BikeStationNode] = []
    for node in nodes:
        in_semicircle = True
        node = node["node"]
        spacesAvailable = 1
        id = node["place"].get("id")
        if not id:
            continue
        capacity = bike_station_capacities[id]
        if capacity is not None:
            spacesAvailable = (capacity - node["place"].get("bikesAvailable", 0)) / capacity

        if spacesAvailable == 0:
            continue
        
        vectorDestinationStation = np.asarray([node["place"]["latitude"], node["place"]["longitude"]]) - np.asarray(destination)
        
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
