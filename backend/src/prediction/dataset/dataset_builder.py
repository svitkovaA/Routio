"""
file: dataset_builder.py

Builds the full feature tensor used for bike availability prediction.
"""
import asyncio
from typing import Dict, Tuple
from service.gbfs_service import GBFSService
import numpy as np
from service.population_service import PopulationService
from service.database_service import DatabaseService
from service.gtfs_service import GTFSService
from prediction.dataset.static_features import compute_static_features
from prediction.dataset.spatial_features import compute_neighbor_features
from prediction.dataset.weather_features import get_weather_array
from prediction.dataset.time_features import build_time_features
from prediction.dataset.bike_data import build_station_matrix
from database.db import init_pool, close_pool

async def get_features() -> Tuple[
    np.ndarray,
    np.ndarray,
    Dict[str, float],
    Dict[str, float]
]:
    """
    Builds the feature tensor for prediction.

    Returns:
        Tuple, containing (array with shape (time steps, stations, features),
        station coordinates, means and standart deviations)
    """
    # Initialize database connection pool
    await init_pool()

    # Load all necessary service states
    database_service = DatabaseService.get_instance()

    await asyncio.gather(
        GTFSService.get_instance().reload(),
        PopulationService.get_instance().reload(),
        GBFSService.get_instance().reload()
    )
    await database_service.reload()

    # Retrieve station information
    station_ids, station_coordinates, weather_map = database_service.get_station_info()

    # -----------------
    # Bicycle info
    # -----------------
    # Loads bicycle time series
    bike_df = await database_service.get_station_timeseries(station_ids)

    # Converts records into station x time matrix
    dataset = build_station_matrix(bike_df)

    # -----------------
    # Time features
    # -----------------
    # Loads time features in format (hour_sin, hour_cos, is_workday, weekday_sin, weekday_cos)
    time_features = build_time_features(dataset.index)

    # -----------------
    # Spatial features
    # -----------------
    # Weighted bike counts from nearby stations
    neighbor_array = compute_neighbor_features(dataset, station_coordinates)

    # -----------------
    # Static features
    # -----------------
    # Computes stops, population density and stations lat and lon
    static_features = compute_static_features(station_coordinates, len(dataset.index))

    # -----------------
    # Convert feature blocks to arrays
    # -----------------
    # Shape (time, stations, features)
    # (time, stations, temperature, wind_speed, clouds, weather_clear, weather_clouds, weather_rain, weather_snow, weather_fog)
    weather_array, normalization_means, normalization_stds = await get_weather_array(
        station_ids,
        weather_map,
        dataset.index,
        database_service.get_weather_timeseries
    )

    # Shape: (time, stations, 1)
    bike_array = dataset.values[..., None]

    # Shape: (time, 1, time_features)
    time_array = time_features.values[:, None, :]

    # Expand time features to all stations
    # (time, stations, hour_sin, hour_cos, is_workday, weekday_sin, weekday_cos)
    # Shape: (time, stations, time_features)
    time_array = np.repeat(time_array, len(station_ids), axis=1)
        
    # Concatenate all features
    # Shape (time, stations, features)
    features_tensor = np.concatenate(
        [bike_array, weather_array, time_array, static_features, neighbor_array],
        axis=2
    )

    # Close database connection pool
    await close_pool()

    return features_tensor, station_coordinates, normalization_means, normalization_stds

if __name__ == "__main__":
    asyncio.run(get_features())

# End of file dataset_builder.py
    