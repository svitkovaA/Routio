"""
file: load_bicycles.py

Loader for bicycle availability time series.
"""

from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Set, Tuple
import httpx
from service.gbfs_service import GBFSService
from config.db import PRODUCTION, PRODUCTION_WINDOW_DAYS
from config.lissy_ben import BEN_NEXTBIKE_URL, BEN_API_KEY
import asyncpg                  # type: ignore[import-untyped]

# Maximum API query window (12 hours)
WINDOW_SEC = 12 * 60 * 60

# Initial timestamp for historical data loading
START_DATETIME = (
    datetime.now(tz=timezone.utc) - timedelta(days=PRODUCTION_WINDOW_DAYS, hours=1)
    if PRODUCTION
    else datetime(2026, 4, 6, tzinfo=timezone.utc)
)
START_TS = int(START_DATETIME.timestamp())

def now_sec() -> int:
    """
    Returns current unix timestamp in seconds.
    """
    return int(datetime.now(tz=timezone.utc).timestamp())

async def load_bicycles(conn: asyncpg.Connection) -> None:
    # Get the latest stored timestamp for this station
    last_complete_ts = await conn.fetchval(
        """
        SELECT MAX(unix_timestamp)
        FROM bicycle
        """
    )

    start = START_TS if last_complete_ts is None else int(last_complete_ts / 1000) + 1
    end_now = now_sec()

    if start >= end_now:
        print("Bicycle data is up to date")
        return
    
    # Service used to validate station identifiers
    gbfs_service = GBFSService.get_instance()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Download data using time windows
        while start < end_now:
            end = min(start + WINDOW_SEC, end_now)

            dt_start = datetime.fromtimestamp(start, tz=timezone.utc)
            start_iso = dt_start.isoformat(timespec='milliseconds')
            start_iso = re.sub(r'\+\d{2}:\d{2}$', 'Z', start_iso)

            dt_end = datetime.fromtimestamp(end, tz=timezone.utc)
            end_iso = dt_end.isoformat(timespec='milliseconds')
            end_iso = re.sub(r'\+\d{2}:\d{2}$', 'Z', end_iso)

            print(start_iso, end_iso)

            # Request bicycle availability
            response = await client.get(
                BEN_NEXTBIKE_URL,
                headers={
                    "Authorization": BEN_API_KEY
                },
                params={
                    "dateFrom": start_iso,
                    "dateTo": end_iso,
                    "fields": '["lat","lng","uid","bikes","bikes_available_to_rent","ben"]'
                }
            )
            response.raise_for_status()

            # Response structure timestamp -> bikes
            data: List[Dict[str, Any]] = response.json()
            if not data:
                start = end
                print(data)
                continue

            station_values: Set[Tuple[int, float, float]] = set()
            bicycle_values: List[Tuple[int, int, int]] = []

            for record in data:
                station_id = record["uid"]

                if not gbfs_service.valid_station_id(str(station_id)):
                    continue

                lat = record["lat"]
                lon = record["lng"]

                ts_iso = record["ben"]["timestamp"]
                dt = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
                unix_ts = int(dt.timestamp() * 1000)

                bikes = record["bikes_available_to_rent"]

                station_values.add((station_id, lat, lon))

                bicycle_values.append(
                    (
                        station_id,
                        unix_ts,
                        bikes,
                    )
                )

            if station_values:
                await conn.executemany(
                    """
                    INSERT INTO station (station_id, latitude, longitude)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (station_id) DO NOTHING
                    """,
                    station_values,
                )

            if bicycle_values:
                await conn.executemany(
                    """
                    INSERT INTO bicycle (station_id, unix_timestamp, available_bicycles)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (station_id, unix_timestamp)
                    DO UPDATE SET
                        available_bicycles = EXCLUDED.available_bicycles
                    """,
                    bicycle_values,
                )

            print(f"Inserted {len(bicycle_values)} records [{start} -> {end}]")

            # Move to next time window
            start = end

# End of file load_bicycles.py
