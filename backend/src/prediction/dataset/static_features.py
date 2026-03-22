"""
file: static_features.py

Computation of static spatial features for bike stations.
"""

from typing import List
import numpy as np
from config.datasets import IDS_JMK_AGENCY_NAME
from service.gtfs_service import GTFSService
from service.population_service import PopulationService

# Earth radius in meters
EARTH_RADIUS: float = 6371000

# Maximum distance considered as a station stop radius
STOP_THRESHOLD: float = 500

# Radius converted to radians
RADIUS: float = STOP_THRESHOLD / EARTH_RADIUS

def normalize_values(values: List[float] | np.ndarray) -> np.ndarray:
    """
    Applies min max normalization to a list of values.

    Args:
        values: Input numeric values

    Returns:
        Normalized values in range (0,1)
    """
    # Convert input values to numpy array
    normalized_values = np.array(values, dtype=np.float32)

    # Apply min max normalization
    normalized_values = (normalized_values - normalized_values.min()) / (
        normalized_values.max() - normalized_values.min() + 1e-6
    )

    return normalized_values

def compute_static_features(
    station_coordinates: np.ndarray,
    time_length: int
) -> np.ndarray:
    """
    Computes static spatial features for all stations.

    Args:
        station_info: List of tuples (station_id, latitude, longitude)
        time_index: Time index used to match dataset length

    Returns:
        Array with shape (time, stations, features)
    """
    # Build spatial index of public transport stops
    tree = GTFSService.get_instance().get_stops_tree(IDS_JMK_AGENCY_NAME)

    # Compute public transport stop density around each station
    stops_density: List[float] = []
    for lat, lon in station_coordinates:
        ref = np.radians([[lat, lon]])

        # Query nearby stops within threshold radius
        _, distances = tree.query_radius(
            ref,
            r=RADIUS,
            return_distance=True
        )

        # Convert distances to meters
        dists = distances[0] * EARTH_RADIUS

        # Distance weighted density
        density = sum(
            max(0, 1 - distance / STOP_THRESHOLD)
            for distance in dists
        )

        stops_density.append(density)

    # Get population service instance
    population_service = PopulationService.get_instance()

    # Compute population density for each station
    population_values: List[float] = []
    for lat, lon in station_coordinates:
        pop = population_service.population_density(lat, lon)
        population_values.append(pop)

    # Extract latitude and longitude features
    lat_values = station_coordinates[:,0]
    lon_values = station_coordinates[:,1]

    # Combine all static features into matrix (stations, features)
    static_features = np.stack([
        normalize_values(stops_density),
        normalize_values(population_values),
        normalize_values(lat_values),
        normalize_values(lon_values)
    ], axis=1)

    # Add time dimension (1, stations, features)
    static_features = static_features[None, :, :]

    # Repeat features across the entire time axis
    static_features = np.repeat(
        static_features,
        time_length,
        axis=0
    )

    return static_features

# End of file static_features.py
