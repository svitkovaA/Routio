"""
file: plots.py

Visualization utilities for evaluating bicycle demand predictions.
"""

from typing import Iterable
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import contextily as ctx
import geopandas as gpd
from matplotlib.colors import Normalize

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

def plot_rmse_map(
    lats: np.ndarray,
    lons: np.ndarray,
    rmse: np.ndarray,
    title: str = "RMSE per station"
) -> None:
    """
    Plot RMSE values for stations on a map.

    Args:
        lats: Array of station latitudes
        lons: Array of station longitudes
        rmse: RMSE values corresponding to each station
        title: Title of the plot
    """

    # Create GeoDataFrame with point geometries
    gdf = gpd.GeoDataFrame(
        {'rmse': rmse},
        geometry=gpd.points_from_xy(lons, lats),
        crs="EPSG:4326"
    )

    # Convert to Web Mercator
    gdf = gdf.to_crs(epsg=3857)

    # Normalize RMSE values for color mapping
    norm = Normalize(vmin=np.min(rmse), vmax=np.max(rmse))

    # Plot stations colored by RMSE
    _, ax = plt.subplots(figsize=(10, 8))

    gdf.plot(
        ax=ax,
        column='rmse',      # Color for coloring stations
        cmap='RdYlGn_r',    # Green to red colors
        legend=True,        # Show colorbar
        markersize=60,      # Size of points on map
        alpha=0.8,          # Transparency
        norm=norm           # Apply normalization
    )

    # Add map tiles
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

    ax.set_title(title)
    ax.set_axis_off()

    plt.tight_layout()

    save_dir = Path("../prediction_results/map/")
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / "rmse_map.png"
    plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.close()

    print(f"Plot saved to {save_path}")

# End of file plots.py
