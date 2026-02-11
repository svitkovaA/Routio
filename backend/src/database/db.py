import asyncpg  # type: ignore[import-untyped]
from contextlib import asynccontextmanager
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_DATABASE
# from .osm import load_bike_racks, bike_racks_empty
from .load_weather import load_weather
from .load_station import stations
from .load_weather_stations import weather_stations
from .create_db import create_tables
from .load_bicycle import load_bicycle_records

pool: asyncpg.Pool | None = None

async def init_pool():
    global pool

    pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE,
    )

    if DB_PASSWORD == "":
        from .create_db import create_database
        await create_database()

    async with create_conn() as conn:
        await create_tables(conn)


async def close_pool():
    global pool
    if pool is not None:
        await pool.close()

@asynccontextmanager
async def create_conn():
    async with pool.acquire() as conn:
        yield conn

async def database():
    async with create_conn() as conn:
        await weather_stations(conn)

        await stations(conn)

        await load_bicycle_records(conn)

        await load_weather(conn)

# End of file db.py
