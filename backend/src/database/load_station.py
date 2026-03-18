"""
file: load_station.py

Loader for bicycle station data.
"""

from typing import List, TypedDict
from datetime import datetime, timezone
import httpx
from service.gbfs_service import GBFSService
from config.lissy_ben import BEN_API_KEY, BICYCLE_PLACES_URL
import asyncpg  # type: ignore[import-untyped]

# Maximum API query window (48 hours)
WINDOW_MS = 48 * 60 * 60 * 1000

# Initial timestamp for historical data loading
START_MS = int(datetime(2026, 1, 21, tzinfo=timezone.utc).timestamp() * 1000)

class Station(TypedDict):
    """
    Representation of a station record.
    """
    station_uid: int
    position: List[float]

async def stations(conn: asyncpg.Connection) -> None:
    """
    Download station data and insert it into the database.

    Args:
        conn: Active database connection.
    """

    print("Downloading station information")

    # Current timestamp in milliseconds
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    # Service used to validate station identifiers
    gbfs_service = GBFSService.get_instance()

    async with httpx.AsyncClient(timeout=20.0) as client:
        from_ms = START_MS

        # Download data using time windows
        while from_ms < now_ms:
            to_ms = min(from_ms + WINDOW_MS, now_ms)

            try:
                # Request station data
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

                    # Filter valid stations and prepare insert values
                    values = [
                        (value["station_uid"], value["position"][0], value["position"][1])
                        for value in data
                        if gbfs_service.valid_station_id(str(value["station_uid"]))
                    ]

                    # Insert stations into database
                    await conn.executemany(sql, values)     # type: ignore
            except Exception:
                continue

            # Move to the next time window
            from_ms = to_ms
    
    print("Downloaded station information")

# End of file load_station.py
