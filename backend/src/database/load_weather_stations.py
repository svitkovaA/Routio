"""
file: load_weather_stations.py

Loader for weather station data.
"""

from typing import Dict, List
import httpx
from config.lissy_ben import LISSY_API_KEY, WEATHER_POSITIONS_URL
import asyncpg  # type: ignore[import-untyped]

async def weather_stations(conn: asyncpg.Connection) -> None:
    """
    Download weather station locations and store them in the database.

    Args:
        conn: Active database connection.
    """

    # Request weather station positions
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            WEATHER_POSITIONS_URL,
            headers={"Authorization": LISSY_API_KEY},
        )
        r.raise_for_status()

        # Response structure station_id -> [latitude, longitude]
        data: Dict[str, List[float]] = r.json()

    sql = """
        INSERT INTO weather_station (weather_station_id, latitude, longitude)
        VALUES ($1, $2, $3)
        ON CONFLICT (weather_station_id) DO NOTHING
    """

    # Convert API response into database insert values
    values = [
        (int(key), value[0], value[1])
        for key, value in data.items()
    ]

    # Insert weather station records
    await conn.executemany(sql, values)     # type: ignore

# End of file load_weather_stations.py