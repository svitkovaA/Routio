from typing import List, TypedDict
from datetime import datetime, timezone
import httpx
from config.lissy_ben import BEN_API_KEY, BICYCLE_PLACES_URL
import asyncpg  # type: ignore[import-untyped]

WINDOW_MS = 48 * 60 * 60 * 1000  # 48 hours
START_MS = int(datetime(2026, 1, 21, tzinfo=timezone.utc).timestamp() * 1000)

class Station(TypedDict):
    station_uid: int
    position: List[float]

async def stations(conn: asyncpg.Connection) -> None:
    print("Downloading station information")
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    async with httpx.AsyncClient(timeout=20.0) as client:
        from_ms = START_MS

        while from_ms < now_ms:
            to_ms = min(from_ms + WINDOW_MS, now_ms)

            r = await client.get(
                BICYCLE_PLACES_URL,
                params={
                    "from": from_ms,
                    "to": to_ms
                },
                headers={"Authorization": BEN_API_KEY},
            )
            r.raise_for_status()
            data: List[Station] = r.json()

            if data:
                sql = """
                    INSERT INTO station (station_id, latitude, longitude)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (station_id) DO NOTHING
                """

                values = [
                    (value["station_uid"], value["position"][0], value["position"][1])
                    for value in data
                ]

                await conn.executemany(sql, values)     # type: ignore

            from_ms = to_ms
    
    print("Downloaded station information")

# End of file load_station.py
