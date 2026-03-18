"""
file: population_service.py

Service for downloading, loading, and caching population density raster data.
"""

from dataclasses import dataclass
from typing import Any
import requests
import zipfile
import shutil
from config.datasets import POPULATION_DIR, POPULATION_PATH, POPULATION_URL
from service.service_base import ServiceBase
import numpy as np
from pyproj import Transformer
import rasterio                             # type: ignore[import-untyped]
from rasterio.windows import from_bounds    # type: ignore[import-untyped]

@dataclass(frozen=True)
class _PopulationState:
    """
    Internal state of the population service.
    """
    # Open raster dataset
    population_raster: Any

    # Raster data
    population_data: np.ndarray

    # Transformer for converting coordinates in lat, lon format into raster coordinate system
    transformer: Transformer

    # Raster dataset JMK window
    window: Any

class PopulationService(ServiceBase[_PopulationState]):
    """
    Service responsible for loading and caching population density.
    """
    # Raster resolution in meters
    PIXEL_SIZE: int = 100

    # Radius for population aggregation around a station
    POP_RADIUS: int = 500

    # Number of pixels corresponding to POP_RADIUS
    PIXELS: int = POP_RADIUS // PIXEL_SIZE

    def __init__(self):
        """
        Initializes the population service.
        """
        super().__init__()

    async def reload(self) -> None:
        """
        Reloads population data and updates the cached state.
        """
        print("Loading Population density cache")

        new_state = await self.__load_new_state()
        self._set_state(new_state)

    async def __load_new_state(self) -> _PopulationState:
        """
        Loads population raster data and prepares coordinate transformer.

        Returns:
            _PopulationState: Newly loaded population dataset state
        """
        # Download dataset if it does not exist locally
        if not POPULATION_PATH.exists():
            self.__download_population_data()
        
        # Open population raster file
        population_raster = rasterio.open(POPULATION_PATH)
        # Transformer converting WGS84 coordinates to raster CRS
        transformer = Transformer.from_crs(
            "EPSG:4326",
            population_raster.crs,
            always_xy=True
        )

        # JMK bounding box
        minx, miny = transformer.transform(15.5, 48.6)
        maxx, maxy = transformer.transform(17.6, 49.65)

        window = from_bounds(
            minx, miny, maxx, maxy,
            transform=population_raster.transform
        )

        # Read raster values into numpy array
        population_data = population_raster.read(1, window=window)

        return _PopulationState(
            population_raster=population_raster,
            population_data=population_data,
            transformer=transformer,
            window=window
        )

    @staticmethod
    def __download_population_data():
        """
        Downloads and extracts the population raster dataset.
        """
        # Ensure dataset directory exists
        POPULATION_DIR.mkdir(parents=True, exist_ok=True)

        zip_path = POPULATION_DIR / "population.zip"

        # Download zipped dataset
        with requests.get(POPULATION_URL, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Temporary extraction directory
        extract_dir = POPULATION_DIR / "tmp"
        extract_dir.mkdir(exist_ok=True)

        # Extract zip archive
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Locate raster file inside archive
        tif_file = next(extract_dir.rglob("*.tif"))

        # Move raster to final dataset path
        shutil.move(str(tif_file), POPULATION_PATH)

        # Remove temporary files
        shutil.rmtree(extract_dir)
        zip_path.unlink()

    def population_density(self, lat: float, lon: float) -> float:
        """
        Computes weighted population density around given coordinates.

        Args:
            lat: Station latitude
            lon: Station longitude

        Returns:
            Weighted population density value
        """
        state = self._get_state()

        # Convert geographic coordinates to raster CRS
        x, y = state.transformer.transform(lon, lat)

        # Convert coordinates to raster pixel indices
        row, col = state.population_raster.index(x, y)

        row -= int(state.window.row_off)
        col -= int(state.window.col_off)

        total = 0.0

        # Iterate through neighboring pixels
        for i in range(-self.PIXELS, self.PIXELS + 1):
            for j in range(-self.PIXELS, self.PIXELS + 1):

                rr = row + i
                cc = col + j

                # Skip pixels outside raster bounds
                if rr < 0 or cc < 0:
                    continue

                if rr >= state.population_data.shape[0] or cc >= state.population_data.shape[1]:
                    continue

                pop = state.population_data[rr, cc]

                # Skip missing population values
                if np.isnan(pop):
                    continue

                # Compute real distance from station to pixel
                dist = np.sqrt(i*i + j*j) * self.PIXEL_SIZE

                # Skip pixels outside aggregation radius
                if dist > self.POP_RADIUS:
                    continue

                # Distance based weighting
                weight = max(0, 1 - dist / self.POP_RADIUS)

                total += pop * weight

        return total
    
# End of file population_service.py
