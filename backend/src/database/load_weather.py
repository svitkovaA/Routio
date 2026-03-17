"""
file: load_weather.py

Loader for weather time-series data.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import httpx
import asyncpg  # type: ignore[import-untyped]
from config.lissy_ben import LISSY_API_KEY, WEATHER_DATA_URL

# Maximum API query window (48 hours)
WINDOW_MS = 48 * 60 * 60 * 1000

# Initial timestamp for historical data
START_DATETIME = datetime(2026, 1, 21, tzinfo=timezone.utc)
START_TS = int(START_DATETIME.timestamp() * 1000)

def now_ms() -> int:
    """
    Return current unix timestamp in milliseconds.
    """
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)

async def load_weather(conn: asyncpg.Connection) -> None:
    """
    Download weather measurements and store them in the database.

    Args:
        conn: Active database connection.
    """

    # Retrieve all weather station ids from database
    station_rows = await conn.fetch("SELECT weather_station_id FROM weather_station")  # type: ignore
    weather_station_ids: List[int] = [r["weather_station_id"] for r in station_rows]

    if not weather_station_ids:
        raise RuntimeError("Weather station is empty")

    # Determine the last complete timestamp
    last_complete_ts = await conn.fetchval(
        """
        SELECT MIN(max_ts) FROM (
            SELECT weather_station_id, MAX(unix_timestamp) AS max_ts
            FROM weather
            WHERE weather_station_id = ANY($1::int[])
            GROUP BY weather_station_id
        ) t
        """,
        weather_station_ids,
    )

    # Determine start timestamp for the next download
    start = START_TS if last_complete_ts is None else int(last_complete_ts) + 1
    end_now = now_ms()

    # Skip loading if data is already up to date
    if start >= end_now:
        print("Weather is up to date")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Download data using time windows
        while start < end_now:
            end = min(start + WINDOW_MS, end_now)

            # Request weather data
            r = await client.get(
                WEATHER_DATA_URL,
                params={"from": start, "to": end},
                headers={"Authorization": LISSY_API_KEY},
            )
            r.raise_for_status()

            data: Dict[str, Dict[str, Any]] = r.json()
            if not data:
                start = end
                continue

            weather_values: List[Tuple[Any, ...]] = []

            # Parse API response structure
            for ts_str, stations_obj in data.items():
                ts = int(ts_str)

                for station_key, snapshot in stations_obj.items():
                    try:
                        ws_id = int(station_key)
                    except ValueError:
                        continue

                    # Skip stations not present in database
                    if ws_id not in weather_station_ids:
                        continue

                    weather_id = snapshot["weather"][0]["id"]
                    temp = snapshot["main"]["temp"]
                    wind_speed = snapshot["wind"]["speed"]
                    clouds = snapshot["clouds"]["all"]

                    weather_values.append(
                        (
                            ts,
                            ws_id,
                            weather_id,
                            temp,
                            wind_speed,
                            clouds
                        )
                    )

            # Insert weather records into database
            if weather_values:
                await conn.executemany(
                    """
                    INSERT INTO weather (
                        unix_timestamp,
                        weather_station_id,
                        weather_id,
                        temperature,
                        wind_speed,
                        clouds
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (unix_timestamp, weather_station_id)
                    DO UPDATE SET
                        weather_id = EXCLUDED.weather_id,
                        temperature = EXCLUDED.temperature,
                        wind_speed = EXCLUDED.wind_speed,
                        clouds = EXCLUDED.clouds
                    """,
                    weather_values,
                )

            print(f"Processing weather: {len(weather_values)} rows [{start} -> {end}]")

            # Move to the next time window
            start = end

# End of file load_weather.py
