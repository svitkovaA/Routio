"""
file: lightgbm.py

LightGBM based bicycle availability prediction.
"""

import asyncio
import time
from typing import Any, Iterable
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import root_mean_squared_error
from sklearn.metrics import r2_score
from prediction.dataset.dataset_builder import get_features
import matplotlib.pyplot as plt
import numpy as np
import lightgbm as lgb
from pathlib import Path

# Prediction horizon
HORIZON = 4 * 6

def plot_station_time_series(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    N: int,
    T: int,
    station_ids: Iterable[int],
    name: str
) -> None:
    """
    Plot full test time series for selected stations.

    Args:
        y_true: Flattened array containing real bike counts with shape (time_steps * stations)
        y_pred: Flattened array containing predicted bike counts with shape (time_steps * stations)
        N: Number of stations in the dataset
        T: Number of time steps in the test dataset
        station_ids: Iterable containing indices of stations to visualize
        name: Name of experiment used to create output directory
    """

    # Create output directory for storing plots
    Path(f"results/{name}").mkdir(parents=True, exist_ok=True)

    # Reshape flattened arrays back to original structure (time, stations)
    y_true = y_true.reshape(T, N)
    y_pred = y_pred.reshape(T, N)

    # Shift real values by prediction horizon
    y_true_shifted = np.full((T, N), np.nan)
    y_true_shifted[HORIZON:] = y_true[:-HORIZON]

    # Create time axis for plotting
    time_axis = np.arange(T)

    # Generate a separate plot for each selected station
    for station in station_ids:

        plt.figure(figsize=(14,6))

        # Plot real bike availability
        plt.plot(time_axis, y_true_shifted[:, station], label="Real bikes", linewidth=2)

        # Plot predicted bike availability
        plt.plot(time_axis, y_pred[:, station], label="Predicted bikes", linewidth=2)

        plt.xlabel("Time step (10 min)")
        plt.ylabel("Number of bikes")
        plt.title(f"Station {station} - Real vs Predicted")

        plt.legend()
        plt.tight_layout()

        plt.savefig(f"../prediction_results/results/{name}/station_{station}_timeseries.png", dpi=300)
        plt.close()

def build_lightgbm_dataset(
    features: np.ndarray[Any],
    train_ratio: float = 0.8,
    horizon: int = 1
):
    """
    Convert spatio temporal dataset into format for LightGBM

    Args:
        features: Feature tensor with shape (time, stations, features)
        train_ratio: Ratio used to split train and test dataset
        horizon: Prediction horizon in time steps

    Returns:
        Tuple, containing (training feature matrix, test feature matrix, test
        targets, num of time steps in test set)
    """
    # Dataset dimensions
    T, N, _ = features.shape

    # Skip initial timesteps required for lag features
    start = 144

    # Last usable timestep
    end = T- horizon

    # All non bike features
    base = features[start:end, :, 1:]

    # Lag features
    lag_1 = features[start-1:end-1, :, 0:1]
    lag_3 = features[start-3:end-3, :, 0:1]
    lag_6 = features[start-6:end-6, :, 0:1]
    lag_12 = features[start-12:end-12, :, 0:1]
    lag_24 = features[start-24:end-24, :, 0:1]
    lag_144 = features[start-144:end-144, :, 0:1]

    # Rolling average feature
    rolling_3 = (lag_1 + lag_3 + lag_6) / 3

    # Combine all features
    X = np.concatenate(
        [base, lag_1, lag_3, lag_6, lag_12, lag_24, lag_144, rolling_3],
        axis=2
    )

    # Bike availability at future timestep
    print("y start: ", start + horizon, ", y end: ", end + horizon)
    y = features[start + horizon:end + horizon, :, 0]

    # Dataset split
    split_t = int((end - start) * train_ratio)

    # Split features
    X_train = X[:split_t]
    X_test = X[split_t:]

    # Split targets
    y_train = y[:split_t]
    y_test = y[split_t:]

    # Convert (time, stations) to (samples)
    X_train = X_train.reshape(-1, X_train.shape[2]).astype(np.float32)
    X_test = X_test.reshape(-1, X_test.shape[2]).astype(np.float32)

    # Flattened targets
    y_train = y_train.reshape(-1)
    y_test = y_test.reshape(-1)

    return X_train, X_test, y_train, y_test, X_test.shape[0] // N

def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    threshold: float
) -> None:
    """
    Evaluate regression and classification performance.

    Args:
        y_true: Real bike counts
        y_pred: Predicted bike counts
        threshold: Threshold defining bike availability
    """
    # Prevent negative predictions
    y_pred = np.clip(y_pred, 0, None)

    # Convert regression to availability prediction
    y_true_bin = (y_true >= threshold).astype(int)
    y_pred_bin = (y_pred >= threshold).astype(int)

    # Count statistics
    false_positive = np.sum((y_true_bin == 0) & (y_pred_bin == 1))
    true_negative = np.sum((y_true_bin == 0) & (y_pred_bin == 0))
    false_negative = np.sum((y_true_bin == 1) & (y_pred_bin == 0))
    true_positive = np.sum((y_true_bin == 1) & (y_pred_bin == 1))

    print("True Positive (bike available correctly predicted):", true_positive)
    print("False Positive (predicted bike but station empty):", false_positive)
    print("False Negative (predicted empty but bike was available):", false_negative)
    print("True Negative (empty correctly predicted):", true_negative)

    total_empty = np.sum(y_true_bin == 0)

    print(
        "Stations predicted with bike but actually empty:",
        false_positive,
        "(",
        false_positive / total_empty * 100,
        "% )"
    )

    # Regression metrics
    print("MAE:", mean_absolute_error(y_true, y_pred))
    print("RMSE:", root_mean_squared_error(y_true, y_pred))
    print("R2:", r2_score(y_true, y_pred))

# Names of all model features
FEATURE_NAMES = [
    "temperature",
    "wind_speed",
    "clouds",
    "weather_clear",
    "weather_clouds",
    "weather_rain",
    "weather_snow",
    "weather_fog",
    "hour_sin",
    "hour_cos",
    "is_workday",
    "weekday_sin",
    "weekday_cos",
    "stops_density",
    "population_density",
    "station_lat",
    "station_lon",
    "neighbor_weighted_lag1",
    "lag_1",
    "lag_3",
    "lag_6",
    "lag_12",
    "lag_24",
    "lag_144",
    "rolling_3"
]

async def lightgbm():
    """
    Train and evaluate LightGBM regression model.
    """
    print("Loading features")

    # Load dataset features
    features, _, _, _ = await get_features()

    # Convert feature tensor into dataset for LightGBM
    X_train, X_test, y_train, y_test, T_test = build_lightgbm_dataset(features, horizon=HORIZON)

    # Performance counter
    start = time.perf_counter()
    print("Trening GB")

    # Initialize LightGBM regressor
    model = lgb.LGBMRegressor(
        n_estimators=1000,
        learning_rate=0.03,
        num_leaves=128,
        max_depth=-1,
        min_child_samples=50,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        max_bin=512,
        n_jobs=-1
    )

    # Train model on prepared dataset
    model.fit(
        X_train,
        y_train,
        feature_name=FEATURE_NAMES
    )

    end = time.perf_counter()
    print(f"Training time: {end - start:.4f} sec")

    # Predict bike availability
    pred = model.predict(X_test)

    # Evaluate metrics
    evaluate_predictions(y_test, pred, threshold=0.8)

    # Extract number of stations
    _, N, _ = features.shape

    # Plot predicted vs real bike counts for selected stations
    plot_station_time_series(
        y_test,
        pred,
        N=N,
        T=T_test,
        station_ids=[0,1,2,3,4,5,6],
        name="lightgbm"
    )

if __name__ == "__main__":
    asyncio.run(lightgbm())

# End of file lightgbm.py
