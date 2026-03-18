"""
file: tcn.py

This module implements a deep learning model TCN for forecasting the number
of bicycles at multiple stations.
"""

import asyncio
import time
from typing import Any, Dict, List, Tuple
import numpy as np
import torch
from torch.utils.data import Dataset
import torch.nn as nn
from torch.utils.data import DataLoader
import torch.optim as optim
from sklearn.metrics import mean_squared_error, r2_score
from torch.nn.utils.parametrizations import weight_norm
from prediction.dataset.dataset_builder import get_features

# Number of past time steps used as input sequence
PAST_STEPS = 144

# Number of future time steps the model predicts
HORIZON = 24 * 6

# Creates training dataset using sliding window
class BikeDataset(Dataset[Tuple[torch.Tensor, torch.Tensor]]):
    """
    Dataset for bicycle demand forecasting using a sliding window approach.
    """
    def __init__(
        self,
        features: np.ndarray[Any],
        past_steps: int = 144,
        horizon: int = 24,
        bike_mean: float | None = None,
        bike_std: float | None = None
    ):
        """
        Initializes the dataset.

        Args:
            features: Input feature tensor with shape (time steps, stations, features)
            past_steps: Number of past time steps used as model input
            horizon: Number of future time steps the model should predict
            bike_mean: Mean value used for normalization of bike counts
            bike_std: Standard deviation used for normalization of bike counts
        """
        # Converts numpy data to pytorch tensor
        self.features = torch.tensor(features).float()

        self.past_steps = past_steps
        self.horizon = horizon

        # Extract bike count feature
        self.bikes = self.features[:, :, 0]

        # Mean and standard deviation used for normalization
        self.bike_mean = bike_mean
        self.bike_std = bike_std

        # Total number of training samples that can be created
        self.length = len(features) - past_steps - horizon

    def __len__(self) -> int:
        """
        Returns the number of samples available in the dataset.

        Returns:
            int: Number of sliding window samples
        """
        # Returns the total number of available samples
        return self.length

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Retrieve one dataset sample.

        Args:
            idx: Index of the sample

        Returns:
            Tuple containing (input tensor with shape (past steps, stations, features),
            output tensor with shape (stations, horizon))
        """
        # Support negative indexing
        if idx < 0:
            idx = self.length + idx

        # Current time index where prediction starts
        i = idx + self.past_steps

        # Input sequence, past observations
        x: torch.Tensor = self.features[i-self.past_steps:i].clone()

        # Normalizes bike count
        if self.bike_mean is not None and self.bike_std is not None:
            x[:, :, 0] = (x[:, :, 0] - self.bike_mean) / self.bike_std

        # Target sequence, future bike counts
        y: torch.Tensor = self.bikes[i:i + self.horizon].T

        # Normalizes target values
        if self.bike_mean is not None and self.bike_std is not None:
            y = (y - self.bike_mean) / self.bike_std

        # Returns input output pair
        return x, y

class Chomp1d(nn.Module):
    """
    Removes padding made by causal convolution.
    """
    def __init__(self, chomp_size: int):
        """
        Initialize the chomp layer.

        Args:
            chomp_size: Number of time steps to remove from the end
        """
        super().__init__()

        self.chomp_size = chomp_size

    def forward(self, x: torch.Tensor):
        """
        Forward pass of the layer.

        Args:
            x: Input tensor with shape (batch, channels, time)

        Returns:
            Tensor with truncated time dimension
        """
        if self.chomp_size == 0:
            return x

        return x[:, :, :-self.chomp_size].contiguous()

class TemporalBlock(nn.Module):
    """
    Single residual block used in the TCN.
    """
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        dilation: int
    ):
        """
        Initializes the temporal block.

        Args:
            in_channels: Number of input feature channels
            out_channels: Number of output feature channels
            kernel_size: Size of the convolution kernel
            dilation: Dilation factor controlling temporal spacing
        """
        super().__init__()

        # Padding needed to keep causal structure
        padding = (kernel_size - 1) * dilation

        # Single causal convolution
        self.conv = weight_norm(
            nn.Conv1d(
                in_channels,
                out_channels,
                kernel_size,
                padding=padding,
                dilation=dilation
            )
        )

        # Remove extra padded timestamps
        self.chomp = Chomp1d(padding)

        # Activation unit, max(0, x)
        self.relu = nn.ReLU()

        # Prevent overfitting
        self.dropout = nn.Dropout(0.2)

        # Residual projection if channel count changes
        self.downsample = None

        # Ensure same channel length
        if in_channels != out_channels:
            self.downsample = nn.Conv1d(in_channels, out_channels, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the temporal block.

        Args:
            x: Input tensor with shape (batch, channels, time)

        Returns:
            Output tensor with the same temporal length
        """
        # Store original data
        residual = x

        # Apply convolution and weighted norm
        out = self.conv(x)

        # Remove padding to maintain causal structure
        out = self.chomp(out)

        # Add nonlinearity
        out = self.relu(out)

        # Prevent overfitting
        out = self.dropout(out)

        # Match residual channels if needed
        if self.downsample is not None:
            residual = self.downsample(residual)

        # Combine original data with the learn rate
        return self.relu(out + residual)

class TCN(nn.Module):
    """
    Temporal Convolutional Network for multi station time series forecasting.
    """
    def __init__(self, num_features: int, horizon: int=24):
        """
        Initialize the TCN model.

        Args:
            num_features: Number of input features per station
            horizon: Number of future time steps predicted by the model
        """
        super().__init__()

        self.horizon = horizon

        # TCN consisting of several dilates convolutional blocks
        self.tcn = nn.Sequential(
            TemporalBlock(num_features, 64, 3, dilation=1),
            TemporalBlock(64, 64, 3, dilation=2),
            TemporalBlock(64, 64, 3, dilation=4),
            TemporalBlock(64, 64, 3, dilation=8),
            TemporalBlock(64, 64, 3, dilation=16),
            TemporalBlock(64, 64, 3, dilation=32),
        )

        self.fc = nn.Linear(64, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the model.

        Args:
            x: Input tensor with shape (batch, time, stations, features)

        Returns:
            Predicted bike counts with shape (batch, stations, horizon)
        """
        # Input tensor (batch, time, stations, features)
        batch, time, stations, features = x.shape

        # Rearrange to treat each station independently (batch, stations, features, time)
        x = x.permute(0, 2, 3, 1).contiguous()

        # The model requires data in format (batch, channels, time)
        x = x.reshape(batch * stations, features, time)
        x = self.tcn(x)

        # Take last timestep
        x = x[:, :, -1]

        # Predict next horizon values
        x = self.fc(x)

        # Reshape after fc from (batch * stations, horizon) to (batch, stations, horizon)
        x = x.reshape(batch, stations, self.horizon)

        return x

def train_model(features: np.ndarray) -> Tuple[nn.Module, float, float]:
    """
    Train the TCN model.

    Args:
        features: Input dataset with shape (time_steps, stations, features)

    Returns:
        Tuple, containing (trained model, mean value and standart deviation used for normalization)
    """

    device = torch.device(
        "mps" if torch.backends.mps.is_available()
        else "cuda" if torch.cuda.is_available()
        else "cpu"
    )
    print("Device:", device)
    torch.set_float32_matmul_precision("high")

    # Create dataset for computing bike metrics
    dataset = BikeDataset(features, PAST_STEPS, HORIZON)

    print("Dataset size:", len(dataset))
    print("Stations:", features.shape[1])
    print("Features:", features.shape[2])

    # Split dataset, 80% is training, 20% is for validation
    split = int(len(dataset) * 0.8)

    # Store bike count for training data
    train_bikes: List[np.ndarray] = []

    for i in range(split):
        _, y = dataset[i]
        train_bikes.append(y.numpy())

    train_bikes_np: np.ndarray = np.concatenate(train_bikes)

    # Compute mean value and standart deviation for training set
    bike_mean = train_bikes_np.mean()
    bike_std = train_bikes_np.std() + 1e-6

    # Create training dataset
    dataset = BikeDataset(
        features,
        PAST_STEPS,
        HORIZON,
        bike_mean=bike_mean,
        bike_std=bike_std
    )

    # Split dataset to train and test one
    train_dataset = torch.utils.data.Subset(dataset, range(split))
    test_dataset = torch.utils.data.Subset(dataset, range(split, len(dataset)))

    # Split dataset into batches
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, drop_last=True, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)

    # Extract num of features
    num_features = features.shape[2]

    # Create model
    model = TCN(num_features, HORIZON).to(device)

    # Evaluation criterion
    criterion = nn.MSELoss()

    # Optimization algorithm
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    epochs: int = 80
    best_loss: float = float("inf")
    patience: int = 8
    patience_counter: int = 0
    best_state: Dict[str, torch.Tensor] | None = None

    # Iterates over all epochs
    for epoch in range(epochs):
        model.train()
        total_loss = 0

        # Iterates over all training data
        for x, y in train_loader:

            x = x.to(device)
            y = y.to(device)

            optimizer.zero_grad()

            # Compute prediction
            pred = model(x)

            # Compare the predicted value with the real one
            loss = criterion(pred, y)

            # Optimizer find out the error and modifies the weights
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
        
        train_loss = total_loss / len(train_loader)

        # Switch the model to evaluation mode
        model.eval()
        test_loss = 0

        # Iterates over all validation data
        with torch.no_grad():
            for x, y in test_loader:

                x = x.to(device)
                y = y.to(device)

                # Compute prediction
                pred = model(x)

                # Compare the predicted value with the real one
                loss = criterion(pred, y)

                test_loss += loss.item()

        test_loss /= len(test_loader)

        # Retrieved better results in last epoch
        if test_loss < best_loss:
            best_loss = test_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        # Worse result retrieved in last epoch
        else:
            patience_counter += 1

        # Early stopping
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch}")
            break

        if epoch % 5 == 0 or epoch == epochs - 1:

            # Store model predictions from all batches
            all_preds: List[np.ndarray] = []
            # Store targets from all batches
            all_targets: List[np.ndarray] = []

            # Disable gradient computation for evaluation
            with torch.no_grad():
                for x, y in test_loader:

                    x = x.to(device)
                    y = y.to(device)

                    # Run forward pass to run the prediction
                    pred = model(x)

                    all_preds.append(pred.cpu().numpy())
                    all_targets.append(y.cpu().numpy())

            # Concatenate predictions and targets from all batches
            all_preds_np = np.concatenate(all_preds, axis=0)
            all_targets_np = np.concatenate(all_targets, axis=0)

            # Denormalize predictions and targets to real bike counts
            pred_real = all_preds_np * bike_std + bike_mean
            target_real = all_targets_np * bike_std + bike_mean

            # Compute RMSE between predictions and targets
            rmse_bikes = np.sqrt(mean_squared_error(
                target_real.flatten(),
                pred_real.flatten()
            ))

            # Compute coefficient of determination
            r2 = r2_score(
                target_real.reshape(-1),
                pred_real.reshape(-1)
            )

            print(
                f"Epoch {epoch} | "
                f"train: {train_loss:.4f} | "
                f"val_loss: {test_loss:.4f} | "
                f"RMSE: {rmse_bikes:.2f} | "
                f"R2: {r2:.3f}"
            )

        else:

            print(
                f"Epoch {epoch} | "
                f"train: {train_loss:.4f} | "
                f"val_loss: {test_loss:.4f}"
            )

    # Restore best model weights based on validation performance
    if best_state is not None:
        model.load_state_dict(best_state)

    # Return trained model and normalization parameters
    return model, bike_mean, bike_std

async def main():
    """
    Entry point for model training. This function loads features, trains a TCN
    forecasting model and saves the trained model with metadata to file tcn_model.pt
    """
    # Get features from dataset
    features, _, means, stds = await get_features()
    print("Features shape:", features.shape)

    start = time.time()
    # Model training
    model, bike_mean, bike_std = train_model(features)
    print("Training time:", time.time() - start)

    # Save trained model
    torch.save({
        "model_state": model.state_dict(),
        "bike_mean": bike_mean,
        "bike_std": bike_std,
        "past_steps": PAST_STEPS,
        "horizon": HORIZON,
        "num_features": features.shape[2],
        "weather_means": means,
        "weather_stds": stds
    }, "tcn_model.pt")

    print("Model saved")

if __name__ == "__main__":
    asyncio.run(main())

# End of file tcn.py
