"""
file: create_db.py

Database initialization utilities for the prediction service.
"""

import asyncpg                                                      # type: ignore[import-untyped]
from config.db import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_DATABASE

async def create_database():
    """
    Create the application database if it does not already exist.
    """
    # Connect to the default PostgreSQL instance
    conn: asyncpg.Connection = await asyncpg.connect(               # type: ignore
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database="postgres"
    )

    try:
        # Check whether the target database already exists
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", DB_DATABASE)   # type: ignore

        # Create database if it does not exist
        if not exists:
            await conn.execute(f'CREATE DATABASE "{DB_DATABASE}"')  # type: ignore

    finally:
        await conn.close()                                          # type: ignore

async def create_tables(conn: asyncpg.Connection):
    """
    Create all required tables and indexes for the application.

    Args:
        conn: Active asyncpg database connection
    """

    # Enable PostGIS extension for spatial data
    await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Table storing bike station locations
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS station (
        station_id INTEGER PRIMARY KEY,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL
    )
    """)

    # Table storing weather station locations
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS weather_station (
        weather_station_id INTEGER PRIMARY KEY,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL
    )
    """)

    # Time-series table storing bike availability at stations
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS bicycle (
        station_id INTEGER,
        unix_timestamp BIGINT,
        available_bicycles INTEGER NOT NULL,
        PRIMARY KEY (station_id, unix_timestamp),
        FOREIGN KEY (station_id) REFERENCES station(station_id) ON DELETE CASCADE
    )
    """)

    # Weather measurements associated with weather stations
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        weather_station_id INTEGER,
        weather_id INTEGER,
        unix_timestamp BIGINT,
        temperature DOUBLE PRECISION,
        wind_speed DOUBLE PRECISION,
        clouds INTEGER,
        PRIMARY KEY (weather_station_id, unix_timestamp),
        FOREIGN KEY (weather_station_id) REFERENCES weather_station(weather_station_id) ON DELETE CASCADE
    )
    """)

    # Bicycle rack locations imported from OSM
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS bicycle_racks (
        osm_id   BIGINT PRIMARY KEY,
        lat      DOUBLE PRECISION NOT NULL,
        lon      DOUBLE PRECISION NOT NULL,
        capacity INTEGER,
        name     TEXT,
        geom     geometry(Point, 4326)
    )
    """)

    # Spatial index for efficient geographic queries on racks
    await conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_bicycle_racks_geom
        ON bicycle_racks
        USING GIST (geom)
    """)

    # Address points imported from OSM
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS osm_addresses (
        osm_id  BIGINT PRIMARY KEY,
        street  TEXT,
        streetnumber TEXT,
        lat     DOUBLE PRECISION NOT NULL,
        lon     DOUBLE PRECISION NOT NULL,
        geom    geometry(Point, 4326)
    )
    """)

    # Spatial index for fast nearest address queries
    await conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_osm_addresses_geom
        ON osm_addresses
        USING GIST (geom);   
    """)

# End of file create_db.py
