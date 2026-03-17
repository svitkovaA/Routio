"""
file: spatial_features.py

Computation of spatial features for bike stations.
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

# Earth radius in meters
EARTH_RADIUS = 6371000

# Maximum distance considered as a station stop radius
STOP_THRESHOLD = 500

# Radius converted to radians
RADIUS = STOP_THRESHOLD / EARTH_RADIUS

def compute_neighbor_features(
    dataset: pd.DataFrame,
    station_coordinates: np.ndarray
) -> np.ndarray:
    """
    Computes spatial neighbor features for each station.

    Args:
        dataset: DataFrame with shape (time, stations) containing bike counts
        station_info: List of tuples (station_id, latitude, longitude)

    Returns:
        Array of shape (time, stations, 1) with weighted neighbor bike counts
    """

    # Convert coordinates to radians
    coords_rad = np.radians(station_coordinates)

    # Build spatial index using BallTree with haversine metric
    tree = BallTree(coords_rad, metric="haversine")

    # Query all neighboring stations within given radius
    neighbors, distances = tree.query_radius(
        coords_rad,
        r=RADIUS,
        return_distance=True
    )

    # Convert distances from radians to meters
    distances = [d * EARTH_RADIUS for d in distances]

    # Bike counts matrix (time_steps, stations) 
    bike_values = dataset.values
    T, N = bike_values.shape

    # Output array for weighted neighbor aggregation    
    neighbor_weighted = np.zeros((T, N), dtype=np.float32)

    # Iterate over stations
    for i, neigh in enumerate(neighbors):
        dists = distances[i]

        # Remove the station itself from its neighbor list
        mask = neigh != i
        neigh = neigh[mask]
        dists = dists[mask]

        # Skip if no neighbors exist
        if len(neigh) == 0:
            continue

        # Compute distance weights
        weights = 1 / (dists + 1e-6)

        # Normalize weights to sum to 1
        weights = weights / weights.sum()

        # Weighted aggregation of neighbor bike counts
        neighbor_weighted[:, i] = (bike_values[:, neigh] * weights).sum(axis=1)
    
    # Apply lag of one timestep to avoid using future information
    neighbor_weighted_lag1 = np.roll(neighbor_weighted, 1, axis=0)

    # Fix the first timestep
    neighbor_weighted_lag1[0] = neighbor_weighted_lag1[1]

    # Add feature dimension (T, N, 1)
    return neighbor_weighted_lag1[..., None]

# End of file spatial_features.py
