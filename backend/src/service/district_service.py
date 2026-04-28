"""
file: district_service.py

Service for providing data about districts.
"""

from dataclasses import dataclass
from typing import List
import httpx
import json
from service.service_base import ServiceBase
import geopandas as gpd
from geopandas.sindex import SpatialIndex
from shapely.geometry import Point
from config.datasets import DISTRICT_URL, DISTRICT_DIR, DISTRICT_PATH

@dataclass(frozen=True)
class _DistrictState:
    """
    Internal state of the district service.
    """
    
    # GeoDataFrame with district polygons
    district: gpd.GeoDataFrame
    
    # Spatial index
    sindex: SpatialIndex

class DistrictService(ServiceBase[_DistrictState]):
    """
    Service responsible for providing district data.
    """

    def __init__(self):
        super().__init__()

        self.__client = httpx.AsyncClient(
            headers={"User-Agent": "Routio/1.0 (academic project)"},
            timeout=10
        )

    async def _shutdown(self) -> None:
        """
        Gracefully releases service resources.
        """
        return await self.__client.aclose()

    async def reload(self) -> None:
        """
        Reloads district data and replaces the internal cached state.
        """
        print("Loading District cache")
        new_state = await self.__load_new_state()
        self._set_state(new_state)
       
    async def __load_new_state(self) -> _DistrictState:
        """
        Loads district GeoJSON from disk, builds GeoDataFrame and spatial index.

        Returns:
            Loaded district dataset with spatial index
        """
        # Download dataset if not present
        if not DISTRICT_PATH.exists():
            await self.__download_data()
        
        # Load GeoJSON file
        with open(DISTRICT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        features = data["features"]

        # Create GeoDataFrame from GeoJSON
        gdf = gpd.GeoDataFrame.from_features(features)

        # Ensure 'name' column exists
        if "name" not in gdf.columns:
            gdf["name"] = [f.get("name") for f in features]

        # Set coordinate reference system
        gdf = gdf.set_crs(epsg=4326)

        return _DistrictState(
            district=gdf,
            sindex=gdf.sindex
        )

    async def __download_data(self) -> None:
        """
        Downloads district GeoJSON dataset.
        """
        response = await self.__client.get(DISTRICT_URL)
        response.raise_for_status()

        # Ensure directory exists
        DISTRICT_DIR.mkdir(parents=True, exist_ok=True)

        with open(DISTRICT_PATH, "w", encoding="utf-8") as f:
            json.dump(response.json(), f)

    def get_district(self, lat: float, lon: float) -> str | None:
        """
        Returns district name for given geographic coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            District name if found, otherwise None
        """
        state = self._get_state()

        # Create point geometry
        point = Point(lon, lat)

        # Use spatial index to limit candidate polygons
        possible: List[int] = [int(i) for i in state.sindex.intersection(point.bounds)]
        candidates: gpd.GeoDataFrame = state.district.iloc[possible]

        # Precise point-in-polygon check
        match = candidates[candidates.intersects(point)]

        if not match.empty:
            return match.iloc[0]['name']

        return None

# End of file district_service.py
