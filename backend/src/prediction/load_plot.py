"""
file: load_plot.py

Evaluation script for the trained TCN bicycle demand forecasting model.
"""

import asyncio
from typing import List, Tuple
import torch
import numpy as np
from prediction.dataset.dataset_builder import get_features
from prediction.plots import plot_station_time_series_tcn
from prediction.tcn import TCN
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

device = torch.device(
    "mps" if torch.backends.mps.is_available()
    else "cuda" if torch.cuda.is_available()
    else "cpu"
)

# Mapping of prediction horizons to index in forecast vector
horizons = {
    "10min": 0,
    "30min": 2,
    "1h": 5,
    "2h": 11,
    "4h": 23,
    "8h": 47,
    "12h": 71,
    "24h": 143
}

def evaluate_horizon(
    y: np.ndarray,
    pred: np.ndarray,
    step: int
) -> Tuple[float, float, float]:
    """
    Compute evaluation metrics for a specific prediction horizon.

    Args:
        y: Array containing real bike counts with shape (samples, stations, horizon)
        pred: Array containing predicted bike counts with shape (samples, stations, horizon)
        step: Index of the prediction horizon to evaluate

    Returns:
        Tuple, containing (MAE, RMSE, R2)
    """
    # Select specific forecast horizon
    y_h = y[:, :, step].flatten()
    pred_h = pred[:, :, step].flatten()

    # Compute evaluation metrics
    mae = mean_absolute_error(y_h, pred_h)
    rmse = np.sqrt(mean_squared_error(y_h, pred_h))
    r2 = r2_score(y_h, pred_h)

    return mae, rmse, r2

async def general():
    """
    Evaluate the trained TCN model on validation data.
    """
    # Load trained model checkpoint
    checkpoint = torch.load(
        "./tcn_model.pt",
        map_location=device,
        weights_only=False
    )

    # Load normalization parameters and model configuration
    bike_mean = checkpoint["bike_mean"]
    bike_std = checkpoint["bike_std"]
    past_steps = checkpoint["past_steps"]
    horizon = checkpoint["horizon"]
    num_features = checkpoint["num_features"]

    # Load dataset features
    features, _, _, _ = await get_features()

    # Initialize model
    model = TCN(
        num_features=num_features,
        horizon=horizon
    )

    # Load trained weights
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)

    # Switch to evaluation mode
    model.eval()

    # Extract bike count feature
    bikes = features[:, :, 0]

    batch_size = 64

    # Lists for collecting predicted ad real values
    pred_list: List[np.ndarray] = []
    y_list: List[np.ndarray] = []

    # Total number of sliding window samples
    dataset_len = len(features) - past_steps - horizon

    # Split dataset into train/validation parts
    split = int(dataset_len * 0.8)

    # Iterates over validation data
    for i in range(split, dataset_len, batch_size):

        x_batch: List[np.ndarray] = []
        y_batch: List[np.ndarray] = []

        # Create sliding window samples
        for j in range(i, min(i + batch_size, len(features) - past_steps - horizon)):
            # Input window, past observations
            x_batch.append(features[j:j+past_steps])

            # Target values, future horizon
            y_batch.append(bikes[j+past_steps:j+past_steps+horizon].T)

        # Convert batch to tensor
        x_batch_tensor = torch.tensor(np.array(x_batch)).float().to(device)
        x_batch_tensor[:, :, :, 0] = (x_batch_tensor[:, :, :, 0] - bike_mean) / bike_std

        with torch.no_grad():
            # Model prediction
            pred = model(x_batch_tensor).cpu().numpy()

        # Store results
        pred_list.append(pred)
        y_list.append(np.array(y_batch)) 

    # Concatenate all batches into full arrays
    pred = np.concatenate(pred_list, axis=0)
    y = np.concatenate(y_list, axis=0)

    # Denormalize values
    pred = pred * bike_std + bike_mean

    print("pred shape:", pred.shape)
    print("y shape:", y.shape)

    # Evaluate model for each prediction horizon
    for name, step in horizons.items():
        mae, rmse, r2 = evaluate_horizon(y, pred, step)
        print(f"\n{name}")
        print(f"MAE  = {mae:.3f}")
        print(f"RMSE = {rmse:.3f}")
        print(f"R2   = {r2:.3f}")

    # Generate time series plots for selected stations
    for name, step in horizons.items():
        plot_station_time_series_tcn(
            y,
            pred,
            station_ids=[0,1,2,3,4,5,6],
            name=f"tcn_{name}",
            step_ahead=step
        )

if __name__ == "__main__":
    asyncio.run(general())

# End of file load_plot.py
