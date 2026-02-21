from datetime import datetime, timezone
from typing import Dict
import httpx
from config.lissy_ben import BEN_API_KEY, BICYCLE_INFO_URL
import asyncpg  # type: ignore[import-untyped]

WINDOW_MS = 48 * 60 * 60 * 1000  # 48 hours

START_DATETIME = datetime(2026, 1, 21, tzinfo=timezone.utc)
START_TS = int(START_DATETIME.timestamp() * 1000)

def now_ms() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)

async def load_bicycle_records(conn: asyncpg.Connection) -> None:
    rows: list[dict[str, int]] = await conn.fetch("SELECT station_id FROM station")     #type: ignore
    stations: list[int] = [row["station_id"] for row in rows]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for station_id in stations:
            last_ts = await conn.fetchval(
                """
                SELECT MAX(unix_timestamp)
                FROM bicycle
                WHERE station_id = $1
                """,
                station_id,
            )

            if last_ts is None:
                start = START_TS
            else:
                start = last_ts + 1

            end_now = now_ms()

            if start >= end_now:
                print(f"Station {station_id} is up to date")
                continue

            while start < end_now:
                end = min(start + WINDOW_MS, end_now)

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

                data: Dict[str, dict[str, int]] = r.json()

                values = [
                    (
                        station_id,
                        int(ts),
                        record["bikes"],
                    )
                    for ts, record in data.items()
                ]

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

                start = end

# End of file load_bicycle.py
