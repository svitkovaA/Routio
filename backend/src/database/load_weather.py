from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import httpx
import asyncpg  # type: ignore[import-untyped]
from config.lissy_ben import LISSY_API_KEY, WEATHER_DATA_URL

WINDOW_MS = 48 * 60 * 60 * 1000  # 48 hours

START_DATETIME = datetime(2026, 1, 21, tzinfo=timezone.utc)
START_TS = int(START_DATETIME.timestamp() * 1000)

def now_ms() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)

async def load_weather(conn: asyncpg.Connection) -> None:
    station_rows = await conn.fetch("SELECT weather_station_id FROM weather_station")  # type: ignore
    weather_station_ids: List[int] = [r["weather_station_id"] for r in station_rows]

    if not weather_station_ids:
        raise RuntimeError("Weather station is empty")

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

    start = START_TS if last_complete_ts is None else int(last_complete_ts) + 1
    end_now = now_ms()

    if start >= end_now:
        print("Weather is up to date")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        while start < end_now:
            end = min(start + WINDOW_MS, end_now)

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

            for ts_str, stations_obj in data.items():
                ts = int(ts_str)

                for station_key, snapshot in stations_obj.items():
                    try:
                        ws_id = int(station_key)
                    except ValueError:
                        continue

                    if ws_id not in weather_station_ids:
                        continue

                    weather_id = snapshot["weather"][0]["id"]
                    temp = snapshot["main"]["temp"]
                    humidity = snapshot["main"]["humidity"]
                    wind_speed = snapshot["wind"]["speed"]
                    clouds = snapshot["clouds"]["all"]
                    visibility = snapshot.get("visibility")

                    weather_values.append(
                        (
                            ts,
                            ws_id,
                            weather_id,
                            temp,
                            wind_speed,
                            clouds,
                            visibility,
                            humidity,
                        )
                    )

            if weather_values:
                await conn.executemany(
                    """
                    INSERT INTO weather (
                        unix_timestamp,
                        weather_station_id,
                        weather_id,
                        temperature,
                        wind_speed,
                        clouds,
                        visibility,
                        humidity
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (unix_timestamp, weather_station_id)
                    DO UPDATE SET
                        weather_id = EXCLUDED.weather_id,
                        temperature = EXCLUDED.temperature,
                        wind_speed = EXCLUDED.wind_speed,
                        clouds = EXCLUDED.clouds,
                        visibility = EXCLUDED.visibility,
                        humidity = EXCLUDED.humidity
                    """,
                    weather_values,
                )

            print(f"Processing weather: {len(weather_values)} rows [{start} -> {end}]")
            start = end

# End of file load_weather.py
