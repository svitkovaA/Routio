"""
file: prediction_service.py

Service for retrieving and predicting bike availability.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import cast
import numpy as np
import torch
import pandas as pd
from config.db import PRODUCTION_WINDOW_DAYS
from models.route import TZ, BikeStationNode, TripPattern
from prediction.tcn import TCN
from prediction.dataset.weather_features import get_weather_array
from prediction.dataset.static_features import compute_static_features
from prediction.dataset.spatial_features import compute_neighbor_features
from prediction.dataset.time_features import build_time_features
from prediction.dataset.bike_data import build_station_matrix
from service.service_base import ServiceBase
from service.database_service import DatabaseService

@dataclass(frozen=True)
class _PredictionState:
    """
    Internal state of the prediction service.
    """
    # Predicted bike counts for all stations and forecast steps
    predictions: np.ndarray

    # Mapping from station id to prediction array index
    station_index: dict[int, int]

    # Timestamp corresponding to the first prediction step
    base_time: pd.Timestamp

class PredictionService(ServiceBase[_PredictionState]):
    """
    Service responsible for generating bike station predictions.
    """
    FORECAST_STEPS = 24 * 6

    def __init__(self):
        """
        Initializes the prediction service and loads the trained model.
        """
        super().__init__()

        # Database service
        self.__db_service = DatabaseService.get_instance()

        # Load trained model checkpoint
        checkpoint = torch.load(
            "./tcn_model.pt",
            weights_only=False,
            map_location=torch.device("cpu")
        )

        # Load normalization parameters and model configuration
        self.bike_mean = checkpoint["bike_mean"]
        self.bike_std = checkpoint["bike_std"]
        self.past_steps = checkpoint["past_steps"]
        horizon = checkpoint["horizon"]
        num_features = checkpoint["num_features"]
        self.weather_means = checkpoint["weather_means"]
        self.weather_stds = checkpoint["weather_stds"]

        # Initialize the prediction model
        self.model = TCN(
            num_features=num_features,
            horizon=horizon
        )

        # Load trained weights
        self.model.load_state_dict(checkpoint["model_state"])

        # Set model to inference mode
        self.model.eval()

    async def reload(self) -> None:
        """
        Reloads prediction data and updates the internal cached state.
        """
        print("Loading Prediction cache")

        new_state = await self.__load_new_state()
        self._set_state(new_state)

    async def __load_new_state(self) -> _PredictionState:
        """"
        Loads data, builds features, and generates predictions.

        Returns:
            _PredictionState: Newly computed prediction state
        """
        # Retrieve station information and weather mapping
        station_ids, station_coordinates, weather_map = self.__db_service.get_station_info()

        # Load recent bike count timeseries
        bike_df = await self.__db_service.get_station_timeseries(station_ids, last_hours=24 * PRODUCTION_WINDOW_DAYS)

        # Convert raw data into station matrix
        dataset = build_station_matrix(bike_df)

        # Ensure consistent station column order
        dataset = dataset.reindex(columns=station_ids)

        time_index = cast(pd.DatetimeIndex, dataset.index)

        # Build time base features
        time_features = build_time_features(time_index)

        # Compute weighted bike counts from nearby stations
        neighbor_array = compute_neighbor_features(dataset, station_coordinates)

        # Generate static station features
        static_features = compute_static_features(station_coordinates, len(dataset.index))

        # Load and normalize weather features
        weather_array, _, _ = await get_weather_array(
            station_ids,
            weather_map,
            time_index,
            lambda id, means, stds: self.__db_service.get_weather_timeseries(
                id,
                normalization_means=means,
                normalization_stds=stds,
                last_hours=24 * PRODUCTION_WINDOW_DAYS
            ),
            self.weather_means,
            self.weather_stds
        )

        # Normalize bike counts
        bike_array = (dataset.values[..., None] - self.bike_mean) / (self.bike_std + 1e-6)

        # Expand time features to match station dimension
        time_array = time_features.values[:, None, :]

        # Repeat time features for each station
        time_array = np.repeat(time_array, len(station_ids), axis=1)

        # Concatenate all feature groups
        features_tensor = np.concatenate(
            [bike_array, weather_array, time_array, static_features, neighbor_array],
            axis=2
        )

        # Select past window used as model input
        x = features_tensor[-self.past_steps:]

        # Convert features to tensor
        x_tensor = torch.from_numpy(x).float().unsqueeze(0)

        # Run model inference
        with torch.no_grad():
            pred = self.model(x_tensor).cpu().numpy()[0]

        # Denormalize predicted bike counts
        pred = pred * self.bike_std + self.bike_mean

        # Prevent negative predictions
        pred = np.maximum(pred, 0)

        # Build mapping from station id to index
        station_index = {int(sid): i for i, sid in enumerate(dataset.columns)}

        # Compute base time corresponding to first forecast step
        base_time = dataset.index[-1].tz_localize("UTC").tz_convert(TZ) + pd.Timedelta(minutes=10)

        return _PredictionState(
            predictions=pred,
            station_index=station_index,
            base_time=base_time
        )

    def predict_bikes(self, station_id: int, time_cursor: datetime) -> int | None:
        """
        Returns predicted number of bikes for a station at a given time.

        Args:
            station_id: Station identifier
            time_cursor: Target time for prediction

        Returns:
            Predicted number of bikes, or None if unavailable
        """
        # Load prediction state
        state = self._get_state()

        # Resolve station index
        station_index = state.station_index.get(station_id)

        if station_index is None:
            return None

        # Convert target time to timestamp
        target_time = pd.Timestamp(time_cursor)

        # Normalize timezone
        if target_time.tzinfo is None:
            target_time = target_time.tz_localize(TZ)
        else:
            target_time = target_time.tz_convert(TZ)

        # Compute prediction step offset
        step = round((target_time - state.base_time) / pd.Timedelta(minutes=10))

        # Validate step range
        if step < 0 or step >= state.predictions.shape[1]:
            return None

        # Retrieve prediction value
        value = state.predictions[station_index, step]

        # Validate value
        if value is None or np.isnan(value) or np.isinf(value):
            return None
        
        # Return rounded prediction
        return int(round(value))

    def update_pattern_predictions(self, pattern: TripPattern) -> None:
        """
        Updates predicted bike availability for all bike stations within a trip pattern.

        Args:
            pattern: TripPattern containing route legs and bike station data
        """
        for leg in pattern.originalLegs:
            if leg.mode == "wait" and leg.bikeStationInfo is not None:
                time_cursor = leg.aimedStartTime

                # Predict bike availability for each candidate station
                for station in leg.bikeStationInfo.bikeStations:
                    if isinstance(station, BikeStationNode):

                        # Do not predict for past times
                        if time_cursor < datetime.now(tz=TZ):
                            station.place.predictedBikes = None
                        else:
                            prediction = self.predict_bikes(
                                int(station.place.id),
                                time_cursor
                            )
                            if prediction is not None:
                                station.place.predictedBikes = prediction

                # Check selected station and flag if no bikes are expected
                selected = leg.bikeStationInfo.selectedBikeStationIndex
                station = leg.bikeStationInfo.bikeStations[selected]
                if (
                    isinstance(station, BikeStationNode) and
                    station.place.predictedBikes is not None and
                    station.place.predictedBikes == 0
                ):
                    leg.zeroBikesPredicted = True

# End of file prediction_service.py
