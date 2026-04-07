"""
file: db.py

Database connection management and initialization utilities.
"""

import asyncpg                  # type: ignore[import-untyped]
from contextlib import asynccontextmanager
from config.db import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_DATABASE
from .load_weather import load_weather
from .load_station import stations
from .load_weather_stations import weather_stations
from .create_db import create_tables
from .load_bicycle import load_bicycle_records

# Global connection pool used across the application
pool: asyncpg.Pool | None = None

async def init_pool():
    """
    Initialize the database connection pool and ensure schema exists.
    """

    global pool

    # Create connection pool
    pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE,
    )

    # If no password is configured, ensure database exists
    if DB_PASSWORD == "":
        from .create_db import create_database
        await create_database()

    # Create tables
    async with create_conn() as conn:
        await create_tables(conn)


async def close_pool():
    """
    Close the database connection pool.
    """

    global pool

    if pool is not None:
        await pool.close()

@asynccontextmanager
async def create_conn():
    """
    Asynchronous context providing a database connection from the global pool.
    """
    async with pool.acquire() as conn:
        yield conn

async def database():
    """
    Load all required data into the database.
    """
    async with create_conn() as conn:
        pass
        # await weather_stations(conn)

        # await stations(conn)

        # await load_bicycle_records(conn)

        # await load_weather(conn)

        # await load_bike_racks(conn)

# End of file db.py
