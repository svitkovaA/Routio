from typing import Dict, List
import httpx
from config.lissy_ben import LISSY_API_KEY, WEATHER_POSITIONS_URL
import asyncpg  # type: ignore[import-untyped]

async def weather_stations(conn: asyncpg.Connection) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            WEATHER_POSITIONS_URL,
            headers={"Authorization": LISSY_API_KEY},
        )
        r.raise_for_status()
        data: Dict[str, List[float]] = r.json()

    sql = """
        INSERT INTO weather_station (weather_station_id, latitude, longitude)
        VALUES ($1, $2, $3)
        ON CONFLICT (weather_station_id) DO NOTHING
    """

    values = [
        (int(key), value[0], value[1])
        for key, value in data.items()
    ]

    # asyncpg executemany
    await conn.executemany(sql, values)     # type: ignore

# End of file load_weather_stations.py