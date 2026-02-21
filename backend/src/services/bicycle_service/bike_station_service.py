"""
file: bike_station_service.py

Provides selecting and ranking optimal both origin and destination bicycle
stations. Stations are scored using a simple weighted model and the best
candidates are returned for further route construction.
"""

from typing import List, Tuple
import numpy as np
from scipy.spatial.distance import cosine
from gql.client import AsyncClientSession
from models.types import BikeStationNode
from services.otp_service import nearest_bike_stations
from services.gtfs_gbfs_service import bike_station_capacities

async def optimal_origin_bike_station_choice(
    origin: Tuple[float, float], 
    destination: Tuple[float, float], 
    max_distance: int, 
    combination: bool, 
    use_semicircle: bool, 
    session: AsyncClientSession
) -> List[BikeStationNode]:
    """
    Selects and ranks optimal origin bike stations based on a weighted scoring model.
    The function evaluates nearby bike stations relative to the provided coordinates. 
    Each station is scored using a combination of:
        - Angle between coordinates
        - Number of available bikes in station
        - Distance from the origin

    Args:
        origin: Latitude and longitude of the first waypoint
        destination: Latitude and longitude of the second waypoint
        max_distance: Maximum allowed search radius in meters
        combination: True when routing public_bicycle, angle is more important
        use_semicircle: If True, stations located in the opposite direction of travel are filtered out
        session: Asynchronous HTTP session

    Returns:
        Top 10 highest ranked bicycle stations sorted by score in descending order
    """
    print("function: optimal_bike_rack_choice")

    # Retrieve nearby bike stations within the maximum distance
    nodes = await nearest_bike_stations(*origin, session, max_distance)

    # Create vector from origin to destination
    vectorOriginDestination = np.asarray(destination, dtype=np.float64) - np.asarray(origin, dtype=np.float64)

    # Set scoring weights based on the combination parameter
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

    # Iterate over all nodes
    for node in nodes:
        in_semicircle = True
        node = node["node"]

        # Skip stations with no available bicycles
        if node["place"].get("bikesAvailable", 0) == 0:
            continue

        # Create vector from origin to current station
        vectorOriginStation = np.asarray([node["place"]["latitude"], node["place"]["longitude"]], dtype=np.float64) - np.asarray(origin, dtype=np.float64)

        # Keep only stations that lie in the forward direction
        if use_semicircle and combination and np.dot(vectorOriginDestination, vectorOriginStation) <= 0:
            in_semicircle = False

        # Compute cosine similarity between direction vectors
        angle = 1 - cosine(vectorOriginDestination, vectorOriginStation)
        # Normalize angle to range (0,1)
        normalizedAngle = (angle + 1) * 0.5

        # Compute final weighted score
        score: float = angleW * normalizedAngle + bikesAvailableW * np.clip(node["place"].get("bikesAvailable", 0), 0, 5) * 0.2 + distanceW * (max_distance - node["distance"]) / max_distance

        # Store score
        node["score"] = score
        if not in_semicircle:
            trashed_nodes.append(node)
        else:
            scoredNodes.append(node)

    # If all stations were filtered out by semicircle constraint use previously discarded stations
    if len(scoredNodes) == 0:
        scoredNodes = trashed_nodes

    # Sort stations by descending score
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
    """
    Selects and ranks optimal destination bike stations based on a weighted scoring model.
    The function evaluates nearby bike stations relative to the provided coordinates. 
    Each station is scored based on:
        - Angle between coordinates
        - Available docking spaces
        - Distance from the destination

    Args:
        origin: Latitude and longitude of the first waypoint
        destination: Latitude and longitude of the second waypoint
        max_distance: Maximum allowed search radius in meters
        combination: True when routing bicycle_public, angle is more important
        use_semicircle: If True, stations located in the opposite direction of travel are filtered out
        session: Asynchronous HTTP session
    
    Returns:
        Top 10 highest ranked bicycle stations sorted by score in descending order
    """
    print("function: optimal_destination_bike_station_choice")

    # Retrieve nearby bike stations within the maximum distance
    nodes = await nearest_bike_stations(*destination, session, max_distance)

    # Create vector from destination to origin
    vectorDestinationOrigin = np.asarray(origin) - np.asarray(destination)

    # Set scoring weights based on the combination parameter
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

    # Iterate over all nodes
    for node in nodes:
        in_semicircle = True
        node = node["node"]

        # Default available space ratio
        spacesAvailable = 1
    
        # Station id is required to retrieve capacity
        id = node["place"].get("id")
        if not id:
            continue

        # Get station capacity from preloaded dictionary
        capacity = bike_station_capacities[id]

        # Compute normalized free docking space ratio
        if capacity is not None:
            spacesAvailable = (capacity - node["place"].get("bikesAvailable", 0)) / capacity

        # Skip stations with no free docking space
        if spacesAvailable == 0:
            continue
        
        # Create vector from destination to current station
        vectorDestinationStation = np.asarray([node["place"]["latitude"], node["place"]["longitude"]]) - np.asarray(destination)
        
        # Keep only stations in the forward direction
        if use_semicircle and combination and np.dot(vectorDestinationOrigin, vectorDestinationStation) <= 0:
            in_semicircle = False

        # Compute cosine similarity between direction vectors
        angle = 1 - cosine(vectorDestinationOrigin, vectorDestinationStation)
        # Normalize angle to range (0, 1)
        normalizedAngle = (angle + 1) * 0.5

        # Compute final weighted score
        score: float = angleW * normalizedAngle + spacesAvailableW * spacesAvailable + distanceW * (max_distance - node["distance"]) / max_distance
    
        # Store score
        node["score"] = score
        if not in_semicircle:
            trashed_nodes.append(node)
        else:
            scoredNodes.append(node)

    # If all stations were filtered out by semicircle constraint use previously discarded stations
    if len(scoredNodes) == 0:
        scoredNodes = trashed_nodes

    # Sort stations by descending score
    sortedNodes = sorted(scoredNodes, key=lambda x: x["score"], reverse=True)

    return sortedNodes[:10]

# End of file bike_station_service.py
