"""
file: db.py

Database connection management and initialization utilities.
"""

import asyncpg                  # type: ignore[import-untyped]
from contextlib import asynccontextmanager
from config.db import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_DATABASE
from database.create_db import create_tables
from database.load_bicycles import load_bicycles
from database.load_weather import load_weather

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

async def database() -> None:
    """
    Load all required data into the database.
    """
    async with create_conn() as conn:

        await load_bicycles(conn)

        await load_weather(conn)

# End of file db.py
