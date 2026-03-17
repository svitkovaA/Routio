"""
file: load_bicycle.py

Loader for bicycle availability time series.
"""

from datetime import datetime, timezone
from typing import Dict
import httpx
from config.lissy_ben import BEN_API_KEY, BICYCLE_INFO_URL
import asyncpg                  # type: ignore[import-untyped]

# Maximum API query window (48 hours)
WINDOW_MS = 48 * 60 * 60 * 1000

# Initial timestamp for historical data loading
START_DATETIME = datetime(2026, 1, 21, tzinfo=timezone.utc)
START_TS = int(START_DATETIME.timestamp() * 1000)

def now_ms() -> int:
    """
    Returns current unix timestamp in milliseconds.
    """
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)

async def load_bicycle_records(conn: asyncpg.Connection) -> None:
    """
    Load bicycle availability records for all stations.

    Args:
        conn: Active database connection
    """
    # Retrieve all station ids from database
    rows: list[dict[str, int]] = await conn.fetch("SELECT station_id FROM station")     #type: ignore
    stations: list[int] = [row["station_id"] for row in rows]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for station_id in stations:
            # Get the latest stored timestamp for this station
            last_ts = await conn.fetchval(
                """
                SELECT MAX(unix_timestamp)
                FROM bicycle
                WHERE station_id = $1
                """,
                station_id,
            )

            # Determine starting timestamp for data retrieval
            if last_ts is None:
                start = START_TS
            else:
                start = last_ts + 1

            end_now = now_ms()

            # Skip station if data is already up to date
            if start >= end_now:
                print(f"Station {station_id} is up to date")
                continue

            # Download data using time windows
            while start < end_now:
                end = min(start + WINDOW_MS, end_now)

                # Request bicycle availability
                r = await client.get(
                    BICYCLE_INFO_URL,
                    params={
                        "from": start,
                        "to": end,
                        "station_uid": station_id,
                    },
                    headers={"Authorization": BEN_API_KEY},
                )
                r.raise_for_status()

                # Response structure timestamp -> bikes
                data: Dict[str, Dict[str, int]] = r.json()

                # Convert API response into database records
                values = [
                    (
                        station_id,
                        int(ts),
                        record["bikes"],
                    )
                    for ts, record in data.items()
                ]

                # Insert records into database
                if values:
                    await conn.executemany(
                        """
                        INSERT INTO bicycle (station_id, unix_timestamp, available_bicycles)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (station_id, unix_timestamp)
                        DO UPDATE SET
                            available_bicycles = EXCLUDED.available_bicycles
                        """,
                        values,
                    )

                print(f"Station {station_id}: {len(values)} records [{start} -> {end}]")

                # Move to next time window
                start = end

# End of file load_bicycle.py
