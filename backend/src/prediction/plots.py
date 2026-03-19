"""
file: plots.py

Visualization utilities for evaluating bicycle demand predictions.
"""

from typing import Iterable
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def plot_station_time_series_tcn(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    station_ids: Iterable[int],
    name: str,
    step_ahead: int = 23
):
    """
    Plot predicted and real bicycle counts for selected stations.

    Args:
        y_true: Array containing real bike counts with shape (time_steps, stations, horizon)
        y_pred: Array containing predicted bike counts with shape (time_steps, stations, horizon)
        station_ids: Station indices for which the time series should be plotted
        name: Name of the model used for saving plots
        step_ahead: Index of the prediction horizon to visualize
    """
    # Directory where plots will be saved
    save_dir = Path(f"../prediction_results/results/{name}_raw")

    # Create directory if it does not exist
    save_dir.mkdir(parents=True, exist_ok=True)

    # Number of time steps in validation data
    T: int = y_true.shape[0]

    # Time axis aligned with prediction horizon
    time_axis: np.ndarray = np.arange(step_ahead, step_ahead + T)

    # No shift needed for immediate prediction
    if step_ahead == 0:
        y_true_shifted = y_true
    else:
        y_true_shifted = np.full_like(y_true, np.nan)
        y_true_shifted[step_ahead:] = y_true[:-step_ahead]

    for station in station_ids:
        # Plot all results from validation set
        real = y_true_shifted[:, station, step_ahead]
        pred = y_pred[:, station, step_ahead]

        # Plot first day of validation set
        # real = y_true_shifted[:144, station, step_ahead]
        # pred = y_pred[:144, station, step_ahead]
        # time_axis_plot_24 = time_axis[:144]

        plt.figure(figsize=(14,6))

        plt.plot(time_axis, real, label="Real bikes", linewidth=1.5)
        plt.plot(time_axis, pred, label="Predicted bikes", linewidth=1.5)
        # plt.plot(time_axis_plot_24, real, label="Real bikes", linewidth=1.5)
        # plt.plot(time_axis_plot_24, np.round(pred), label="Predicted bikes", linewidth=1.5)

        plt.xlabel("Time step (10 min)")
        plt.ylabel("Number of bikes")
        plt.title(f"Station {station} (4h prediction)")

        plt.legend()
        plt.tight_layout()

        plt.savefig(
            save_dir / f"station_{station}_{step_ahead}.png",
            dpi=300
        )

        plt.close()

# End of file plots.py
