"""
file: time_features.py

File implementing time features for bike prediction.
"""

import numpy as np
import pandas as pd

def build_time_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Generates cyclical time features.

    Args:
        index: Datetime index representing the time axis of the dataset

    Returns:
        DataFrame containing time based features
    """
    # Create feature dataframe using the same time index
    features = pd.DataFrame(index=index)

    # Hour of day in circular representation
    features["hour_sin"] = np.sin(2 * np.pi * index.hour / 24)
    features["hour_cos"] = np.cos(2 * np.pi * index.hour / 24)

    # Working day in circular representation
    features["is_workday"] = (index.weekday < 5).astype(int)

    # Day of week in circular representation
    features["weekday_sin"] = np.sin(2 * np.pi * index.weekday / 7)
    features["weekday_cos"] = np.cos(2 * np.pi * index.weekday / 7)

    return features

# End of file time_features.py
