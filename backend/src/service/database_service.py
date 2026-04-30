"""
file: database_service.py

Service responsible for retrieving and caching station, bicycle, and weather
data from the database.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, cast
import pandas as pd
import time
import numpy as np
from service.weather_service import WeatherService
from config.db import PRODUCTION, PRODUCTION_WINDOW_DAYS
from models.route import TZ
from database.db import create_conn, database
from service.service_base import ServiceBase
from service.gbfs_service import GBFSService

@dataclass(frozen=True)
class _DatabaseState:
    """
    Internal state of the database service.
    """
    # Station coordinates
    station_coordinates: np.ndarray

    # List of station ids
    station_ids: List[int]

    # Maps bike stations to nearest weather stations
    weather_map: Dict[int, int]

class DatabaseService(ServiceBase[_DatabaseState]):
    """
    Service responsible for loading and caching database information.
    """
    def __init__(self):
        super().__init__()

        # GBFS service instance
        self.__gbfs_service = GBFSService.get_instance()

        # Weather service instance
        self.__weather_service = WeatherService.get_instance()

    async def reload(self) -> None:
        """
        Reloads data and replaces the internal cached state.
        """
        new_state = await self.__load_new_state()
        self._set_state(new_state)

    async def __load_new_state(self) -> _DatabaseState:
        """
        Loads station data and weather station mapping.

        Returns:
            _DatabaseState: Newly constructed database state
        """
        if PRODUCTION:
            # Ensure database contains only recent data
            await self.__ensure_db_window()

            # If database is empty, try to initialize it
            if await self.__db_empty():
                await database()

                # If still empty, fallback to runtime loading
                if await self.__db_empty():
                    await self.__runtime_load()

            # Refresh data during runtime
            else:
                await self.__runtime_load()

        else:
            # Download newest data
            await database()

        # Retrieve station ids and coordinates
        station_ids, station_coordinates = await self.__get_station_info()

        # Maps bike stations to nearest weather stations
        weather_map = await self.__get_station_weather_map(station_ids)

        return _DatabaseState(
            station_coordinates=station_coordinates,
            station_ids=station_ids,
            weather_map=weather_map
        )
    
    @staticmethod
    async def __ensure_db_window():
        """
        Removes outdated data from the database based on configured time window.
        """
        threshold_dt = datetime.now(tz=TZ) - timedelta(days=PRODUCTION_WINDOW_DAYS, hours=1)
        threshold_ms = int(threshold_dt.timestamp() * 1000)

        async with create_conn() as conn:
            deleted_bicycle = await conn.execute(
                """
                DELETE FROM bicycle
                WHERE unix_timestamp < $1
                """,
                threshold_ms
            )

            deleted_weather = await conn.execute(
                """
                DELETE FROM weather
                WHERE unix_timestamp < $1
                """,
                threshold_ms
            )

        print(f"Deleted bicycle rows: {deleted_bicycle}")
        print(f"Deleted weather rows: {deleted_weather}")

    @staticmethod
    async def __db_empty() -> bool:
        """
        Checks whether the bicycle table contains any data.

        Returns:
            bool: True if empty, false otherwise
        """
        async with create_conn() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM bicycle LIMIT 1
                );
            """)
        return not exists
    
    async def __load_bicycles(self) -> None:
        """
        Loads bike station data and availability data into the database.
        """
        bicycle_station_info = self.__gbfs_service.get_station_info()

        # Prepare station records
        bicycle_station_rows: List[Tuple[int, float, float]] = [
            (int(item["id"]), item["lat"], item["lon"])                 # type: ignore
            for item in bicycle_station_info
        ]

        # Prepare bike availability rows
        bicycle_rows = self.__gbfs_service.get_bicycle_rows()
        print("bike: ", len(bicycle_rows))
        print("stations: ", len(bicycle_station_rows))

        async with create_conn() as conn:
            await conn.executemany(
                    """
                    INSERT INTO station (station_id, latitude, longitude)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (station_id) DO NOTHING
                    """,
                    bicycle_station_rows,
                )
            
            await conn.executemany(
                    """
                    INSERT INTO bicycle (station_id, unix_timestamp, available_bicycles)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (station_id, unix_timestamp)
                    DO UPDATE SET
                        available_bicycles = EXCLUDED.available_bicycles
                    """,
                    bicycle_rows,
                )

    async def __load_weather(self) -> None:
        """
        Loads weather station data and weather data into the database.
        """
        weather_stations = self.__weather_service.get_stations()
        weather_data = self.__weather_service.get_weather_rows()

        async with create_conn() as conn:
            await conn.executemany(
                """
                INSERT INTO weather_station (weather_station_id, latitude, longitude)
                VALUES ($1, $2, $3)
                ON CONFLICT (weather_station_id) DO NOTHING
                """,
                weather_stations,
            )

            await conn.executemany(
                    """
                    INSERT INTO weather (
                        weather_station_id,
                        weather_id,
                        unix_timestamp,
                        temperature,
                        wind_speed,
                        clouds
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (weather_station_id, unix_timestamp)
                    DO UPDATE SET
                        weather_id = EXCLUDED.weather_id,
                        temperature = EXCLUDED.temperature,
                        wind_speed = EXCLUDED.wind_speed,
                        clouds = EXCLUDED.clouds
                    """,
                    weather_data,
                )

    async def __runtime_load(self) -> None:
        """
        Performs bicycles and weather runtime data update.
        """
        await self.__load_bicycles()
        await self.__load_weather()

    @staticmethod
    async def __get_station_info() -> Tuple[List[int], np.ndarray]:
        """
        Retrieves station identifiers together with their coordinates.

        Returns:
            Tuple containing (List of station ids, List of latitude and longitude)
        """
        # Query stations ordered by number of bicycle records
        async with create_conn() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    b.station_id,
                    s.latitude,
                    s.longitude,
                    COUNT(*) AS records
                FROM public.bicycle b
                JOIN public.station s ON b.station_id = s.station_id
                GROUP BY b.station_id, s.latitude, s.longitude
                ORDER BY records DESC
                """
            )

        station_ids: List[int] = []
        station_coordinates: List[List[float]] = []

        # Extract station ids and coordinates
        for row in rows:
            station_ids.append(row["station_id"])
            station_coordinates.append([row["latitude"], row["longitude"]])

        return (
            station_ids,
            np.array(station_coordinates, dtype=np.float64)
        )

    @staticmethod
    async def __get_station_weather_map(
        station_ids: List[int]
    ) -> Dict[int, int]:
        """
        Maps each bike station to the nearest weather station.

        Args:
            station_ids: List of bike station ids

        Returns:
            Dictionary mapping station_id to weather_station_id
        """
        # Query nearest weather station for each bike station
        async with create_conn() as conn:
            rows = await conn.fetch("""
                SELECT
                    s.station_id,
                    ws.weather_station_id
                FROM station s
                CROSS JOIN LATERAL (
                    SELECT weather_station_id
                    FROM weather_station ws
                    ORDER BY
                        (s.latitude - ws.latitude)^2 +
                        (s.longitude - ws.longitude)^2
                    LIMIT 1
                ) ws
                WHERE s.station_id = ANY($1)
            """, station_ids)

        # Convert rows to dictionary mapping
        return {r["station_id"]: r["weather_station_id"] for r in rows}

    @staticmethod
    async def get_station_timeseries(
        station_ids: List[int],
        last_hours: int | None = None
    ) -> pd.DataFrame:
        """
        Fetches bicycle availability time series for selected stations.

        Args:
            station_ids: List of station ids
            last_hours: If set, returns only last N hours

        Returns:
            Dataframe containing station id, bikes and timestamp
        """
        async with create_conn() as conn:
            # Fetch complete time series
            if last_hours is None:
                db_rows = await conn.fetch("""
                    SELECT station_id, unix_timestamp, available_bicycles
                    FROM bicycle
                    WHERE station_id = ANY($1)
                """, station_ids)

            else:
                # Compute timestamp threshold
                now_ms = int(time.time() * 1000)
                since_ms = now_ms - last_hours * 3600 * 1000

                # Fetch recent time series
                db_rows = await conn.fetch("""
                    SELECT station_id, unix_timestamp, available_bicycles
                    FROM bicycle
                    WHERE station_id = ANY($1)
                    AND unix_timestamp >= $2
                """, station_ids, since_ms)

        # Convert database rows to DataFrame
        timeseries_df = pd.DataFrame(
            db_rows,
            columns=["station_id", "unix_timestamp", "bikes"]
        )

        # Convert unix timestamp to datetime
        timeseries_df["timestamp"] = pd.to_datetime(
            timeseries_df["unix_timestamp"], unit="ms"
        )

        # Remove raw unix timestamp column
        timeseries_df = timeseries_df.drop(columns=["unix_timestamp"])

        return timeseries_df

    @staticmethod
    async def get_weather_timeseries(
        weather_station_id: int,
        normalization_means: Dict[str, float] | None = None,
        normalization_stds: Dict[str, float] | None = None,
        last_hours: int | None = None
    ) -> Tuple[pd.DataFrame, Dict[str, float], Dict[str, float]]:
        """
        Retrieves weather time series for a given weather station.

        Args:
            weather_station_id: Weather station identifier
            normalization_means: Normalization means
            normalization_stds: Normalization standard deviations
            last_hours: If set, returns only last N hours

        Returns:
            Tuple (weather dataframe indexed by timestamp, means and standart deviations for normalization)
        """
        async with create_conn() as conn:
            # Fetch complete weather series
            if last_hours is None:
                rows = await conn.fetch("""
                    SELECT unix_timestamp, weather_id, temperature, wind_speed, clouds
                    FROM weather
                    WHERE weather_station_id=$1
                    ORDER BY unix_timestamp
                """, weather_station_id)

            else:
                # Compute timestamp threshold
                now_ms = int(time.time() * 1000)
                since_ms = now_ms - last_hours * 3600 * 1000

                # Fetch recent weather series
                rows = await conn.fetch("""
                    SELECT unix_timestamp, weather_id, temperature, wind_speed, clouds
                    FROM weather
                    WHERE weather_station_id=$1
                    AND unix_timestamp >= $2
                    ORDER BY unix_timestamp
                """, weather_station_id, since_ms)

        # Convert database rows to DataFrame
        df = pd.DataFrame(
            rows,
            columns=["unix_timestamp", "weather_id", "temperature", "wind_speed", "clouds"]
        )

        # Convert unix timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["unix_timestamp"], unit="ms")

        # Set timestamp as index
        df = df.set_index("timestamp")

        # Map weather codes to simplified categories
        df["weather_type"] = df["weather_id"].apply(DatabaseService.__map_weather)

        # One hot encode weather categories
        weather_onehot = pd.get_dummies(df["weather_type"], prefix="weather")

        # Ensure all columns exist
        for col in ["weather_clear", "weather_clouds", "weather_rain", "weather_snow", "weather_fog"]:
            if col not in weather_onehot:
                weather_onehot[col] = 0

        # Append one hot encoded weather columns
        df = pd.concat([df, weather_onehot], axis=1)

        # Normalize continuous weather variables
        weather_cols = ["temperature", "wind_speed", "clouds"]

        if normalization_means is not None and normalization_stds is not None:
            for col in weather_cols:
                df[col] = (
                    df[col] - normalization_means[col]
                ) / (normalization_stds[col] + 1e-6)

        else:
            # Compute normalization statistics
            normalization_means = cast(Dict[str, float], df[weather_cols].mean().to_dict())
            normalization_stds = cast(Dict[str, float], df[weather_cols].std().to_dict())

            # Normalize weather variables
            df[weather_cols] = (
                df[weather_cols] - df[weather_cols].mean()
            ) / (df[weather_cols].std() + 1e-6)

        # Remove unnecessary columns
        df = df.drop(columns=["weather_type", "weather_id", "unix_timestamp"])

        return df, normalization_means, normalization_stds
    
    @staticmethod
    async def find_bike_racks(lat: float, lon: float, radius: float) -> Any:
        """
        Retrieves bike racks in a given location.

        Args:
            lat: Location latitude
            lon: Location longitude
            radius: Search radius

        Returns:
            Database query results
        """
        async with create_conn() as conn:           # type: ignore
            return await conn.fetch("""
                SELECT
                    osm_id,
                    lat,
                    lon,
                    name,
                    capacity,
                    ST_Distance(
                        geom::geography,
                        ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                    ) AS distance
                FROM bicycle_racks
                WHERE ST_DWithin(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
                    $3
                )
                ORDER BY distance;
            """, lon, lat, radius)                  # type: ignore

    def get_station_info(self) -> Tuple[List[int], np.ndarray, Dict[int, int]]:
        """
        Returns cached station data.

        Returns:
            Tuple (List of station ids, station coordinates, mapping to nearest weather station)
        """
        # Retrieve cached state
        state = self._get_state()

        return (
            state.station_ids,
            state.station_coordinates,
            state.weather_map
        )

    @staticmethod
    def __map_weather(code: int) -> str:
        """
        Maps OpenWeather codes to simplified weather categories.

        Args:
            code: Weather condition code

        Returns:
            Simplified weather category
        """
        if code == 800:
            return "clear"

        if 801 <= code <= 804:
            return "clouds"

        if 300 <= code <= 531:
            return "rain"

        if 600 <= code <= 622:
            return "snow"

        if 700 <= code <= 781:
            return "fog"

        return "other"

# End of file database_service.py
