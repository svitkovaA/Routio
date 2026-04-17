"""
file: load_weather.py

Loads weather and weather stations from BEN.
"""

from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Set, Tuple
import httpx
from urllib.parse import quote
import asyncpg                      # type: ignore[import-untyped]
from config.db import PRODUCTION, PRODUCTION_WINDOW_DAYS
from config.lissy_ben import BEN_API_KEY, BEN_WEATHER_URL

# Maps station names retrieved from API to internal DB ids
STATION_NAME_TO_ID = {
    "Brno": 0,
    "Blansko": 2,
    "Hodonín": 3
}

# Maximum API query window (12 hours)
WINDOW_SEC = 12 * 60 * 60

# Initial timestamp for historical data
START_DATETIME = (
    datetime.now(tz=timezone.utc) - timedelta(days=PRODUCTION_WINDOW_DAYS, hours=1)
    if PRODUCTION
    else datetime(2026, 4, 6, tzinfo=timezone.utc)
)
START_TS = int(START_DATETIME.timestamp())

def now_sec() -> int:
    """
    Return current unix timestamp in seconds.
    """
    return int(datetime.now(tz=timezone.utc).timestamp())

async def load_weather(conn: asyncpg.Connection) -> None:
    """
    Download weather data from BEN API and store it in the database.

    Args:
        conn: Active database connection
    """
    # Determine the last complete timestamp
    last_complete_ts = await conn.fetchval(
        """
        SELECT MAX(unix_timestamp)
        FROM weather
        """
    )

    # Determine start timestamp for the next download
    start = START_TS if last_complete_ts is None else int(last_complete_ts / 1000) + 1
    end_now = now_sec()

    # Skip loading if already up to date
    if start >= end_now:
        print("Weather is up to date")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Iterate over time windows
        while start < end_now:
            end = min(start + WINDOW_SEC, end_now)

            # Convert timestamps to ISO 8601 format
            dt_start = datetime.fromtimestamp(start, tz=timezone.utc)
            start_iso = dt_start.isoformat(timespec='milliseconds')
            start_iso = re.sub(r'\+\d{2}:\d{2}$', 'Z', start_iso)

            dt_end = datetime.fromtimestamp(end, tz=timezone.utc)
            end_iso = dt_end.isoformat(timespec='milliseconds')
            end_iso = re.sub(r'\+\d{2}:\d{2}$', 'Z', end_iso)

            # Request weather data from API
            response = await client.get(
                BEN_WEATHER_URL,
                headers={
                    "Authorization": BEN_API_KEY
                },
                params={
                    "dateFrom": quote(start_iso, safe=":"),
                    "dateTo": quote(end_iso, safe=":"),
                    "fields": '["dt","name","coord","weather","main","wind","clouds"]'
                }
            )
            response.raise_for_status()
            data: List[Dict[str, Any]] = response.json()

            # Skip empty responses
            if not data:
                start = end
                continue

            # Buffers for batch insert
            station_values: Set[Tuple[int, float, float]] = set()
            weather_values: List[Tuple[int, int, int, float, float, int]] = []

            for record in data:
                name = record["name"]

                # Ignore stations not mapped to internal ids
                if name not in STATION_NAME_TO_ID:
                    continue

                station_id = STATION_NAME_TO_ID[name]

                lat = record["coord"]["lat"]
                lon = record["coord"]["lon"]

                station_values.add((station_id, lat, lon))

                # Convert timestamp to milliseconds
                unix_ts = record["dt"] * 1000

                weather_id = record["weather"][0]["id"]
                temp = record["main"]["temp"]
                wind_speed = record["wind"]["speed"]
                clouds = record["clouds"]["all"]

                weather_values.append(
                    (
                        station_id,
                        weather_id,
                        unix_ts,
                        temp,
                        wind_speed,
                        clouds,
                    )
                )

            # Insert weather stations
            if station_values:
                await conn.executemany(
                    """
                    INSERT INTO weather_station (weather_station_id, latitude, longitude)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (weather_station_id) DO NOTHING
                    """,
                    station_values,
                )

            # Insert weather data
            if weather_values:
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
                    weather_values,
                )

            print(f"Inserted {len(weather_values)} weather rows")

            # Move to the next time window
            start = end

# End of file load_weather.py
