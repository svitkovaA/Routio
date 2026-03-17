"""
file: weather_features.py

Utilities for processing and aligning weather data with bike station time series.
"""

from typing import Any, Callable, Coroutine, Dict, List, Tuple
import numpy as np
import pandas as pd

def normalize_weather(
    df: pd.DataFrame,
    target_index: pd.DatetimeIndex
) -> pd.DataFrame:
    """
    Resamples and aligns weather time series with the bike dataset.

    Args:
        df: Raw weather time series
        target_index: Target timestamps

    Returns:
        Weather dataframe resampled to 10-minute intervals
    """
    
    # Resample to fixed 10-minute interval
    df = df.resample("10min").mean()

    # Fill missing values
    df = df.interpolate("time").ffill().bfill()

    # Align timestamps with bike dataset
    df = df.reindex(target_index).interpolate("time").ffill().bfill()

    return df

async def get_weather_array(
    station_ids: List[int],
    weather_map: Dict[int, int],
    target_index: pd.DatetimeIndex,
    get_weather_timeseries: Callable[[int, Dict[str, float] | None, Dict[str, float] | None], Coroutine[Any, Any, Tuple[pd.DataFrame, Dict[str, float], Dict[str, float]]]],
    normalization_means: Dict[str, float] | None = None,
    normalization_stds: Dict[str, float] | None = None
) -> Tuple[np.ndarray,  Dict[str, float],  Dict[str, float]]:
    """
    Retrieve weather data aligned with bike stations.

    Args:
        station_ids: List of bike station identifiers
        weather_map: Mapping from bike station id to weather station id
        target_index: Target timestamps of the bike dataset
        get_weather_timeseries: Async function returning weather dataframe
        normalization_means: Normalization means
        normalization_stds: Normalization standard deviations

    Returns:
        Tuple, containing (weather feature tensor, means and standart
        deviations for normalization)
    """
    # Identify unique weather stations
    weather_ids = set(weather_map.values())

    # Normalize weather time series to match bike timestamps
    weather_dfs: Dict[int, pd.DataFrame] = {}

    for ws_id in weather_ids:
        # Load weather time series for given weather station
        df, means, stds = await get_weather_timeseries(ws_id, normalization_means, normalization_stds)

        # Store normalization parameters if not provided
        if normalization_means is None:
            normalization_means = means
            normalization_stds = stds

        # Normalize and align weather data
        weather_dfs[ws_id] = normalize_weather(df, target_index)

    # Map weather data to each bike station
    station_weather: Dict[int, pd.DataFrame] = {}

    for station_id in station_ids:
        # Find weather station assigned to bike station
        ws_id = weather_map[station_id]

        station_weather[station_id] = weather_dfs[ws_id]

    # Convert weather data to numpy arrays
    weather_arrays: List[np.ndarray] = []

    for sid in station_ids:
        df = station_weather[sid]

        # Extract raw values from dataframe
        weather_arrays.append(df.values)

    # Stack arrays to shape (time, stations, features)
    weather_tensor: np.ndarray = np.stack(weather_arrays, axis=1)
    
    return weather_tensor, normalization_means, normalization_stds

# End of file weather_features.py
