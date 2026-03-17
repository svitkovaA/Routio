"""
file: bike_data.py

Utilities for transforming raw bike availability records into a structured
(time x station) matrix used for model training.
"""

import pandas as pd

def build_station_matrix(timeseries_df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts raw bike records into a station time matrix.

    Args:
        timeseries_df: DataFrame containing bike records

    Returns:
        DataFrame, where index is timestamp, columns are station_ids and values are numbers of bikes
    """

    # Pivot data into time x stations matrix
    dataset = timeseries_df.pivot(
        index="timestamp",
        columns="station_id",
        values="bikes"
    )

    # Resample time series to fixed 10-minute interval
    dataset = dataset.resample("10min").mean()

    # Fill missing values by time interpolation
    dataset = dataset.interpolate("time").ffill().bfill()

    return dataset

# End of file bike_data.py
