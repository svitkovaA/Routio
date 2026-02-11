import asyncpg  # type: ignore[import-untyped]
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_DATABASE

async def create_database():
    conn: asyncpg.Connection = await asyncpg.connect(       # type: ignore
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database="postgres"
    )

    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", DB_DATABASE)   # type: ignore

        if not exists:
            await conn.execute(f'CREATE DATABASE "{DB_DATABASE}"')   # type: ignore

    finally:
        await conn.close()  # type: ignore

async def create_tables(conn: asyncpg.Connection):
    await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS station (
        station_id INTEGER PRIMARY KEY,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL
    )
    """)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS weather_station (
        weather_station_id INTEGER PRIMARY KEY,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL
    )
    """)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS bicycle (
        station_id INTEGER,
        unix_timestamp BIGINT,
        available_bicycles INTEGER NOT NULL,
        PRIMARY KEY (station_id, unix_timestamp),
        FOREIGN KEY (station_id) REFERENCES station(station_id)
    )
    """)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        weather_station_id INTEGER,
        weather_id INTEGER,
        unix_timestamp BIGINT,
        weather_code INTEGER,
        temperature DOUBLE PRECISION,
        wind_speed DOUBLE PRECISION,
        clouds INTEGER,
        visibility INTEGER,
        humidity INTEGER,
        PRIMARY KEY (weather_station_id, unix_timestamp),
        FOREIGN KEY (weather_station_id) REFERENCES weather_station(weather_station_id)
    )
    """)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS bicycle_racks (
        osm_id   BIGINT PRIMARY KEY,
        lat      DOUBLE PRECISION NOT NULL,
        lon      DOUBLE PRECISION NOT NULL,
        capacity INTEGER,
        geom     geometry(Point, 4326)
    )
    """)

    await conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_bicycle_racks_geom
        ON bicycle_racks
        USING GIST (geom)
    """)

# End of file create_db.py
