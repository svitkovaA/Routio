import asyncio
import logging
from services.public_transport_service.lissy import cache_lissy
from database.db import database, bike_racks_empty_wrapper
from services.gtfs_gbfs_service import load_gbfs_data, load_gtfs_data, vehicle_position
from datetime import datetime, timedelta

def seconds_until_next_daily(hour: int, minute: int = 0) -> float:
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()

def seconds_until_next_weekday(weekday: int, hour: int, minute: int = 0) -> float:
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    days_ahead = (weekday - now.weekday()) % 7
    if days_ahead == 0 and target <= now:
        days_ahead = 7

    target = target + timedelta(days=days_ahead)
    return (target - now).total_seconds()

async def vehicle_position_worker():
    """
    Background worker that periodically updates vehicle position data
    """
    while True:
        try:
            # Update vehicle positions
            await vehicle_position()
        except Exception:
            # Log the exception without terminating the worker
            logging.exception("vehicle_position failed")
        # Wait before the next update cycle
        await asyncio.sleep(10)

async def database_worker():
    load_osm_data = await bike_racks_empty_wrapper()
    while True:
        try:
            await database(load_osm_data)
            load_osm_data = True
        except Exception:
            # Log the exception without terminating the worker
            logging.exception("database failed")
        # Wait before the next update cycle
        delay = seconds_until_next_weekday(weekday=0, hour=4, minute=0)  # Monday 04:00
        await asyncio.sleep(delay) # 7 days interval

async def gbfs_worker():
    while True:
        try:
            load_gbfs_data()
        except Exception:
            logging.exception("load_gbfs_data failed")

        delay = seconds_until_next_weekday(weekday=0, hour=4, minute=0)  # Monday 04:00
        await asyncio.sleep(delay)

async def gtfs_worker():
    while True:
        try:
            delay = seconds_until_next_weekday(weekday=0, hour=4, minute=0)  # Monday 04:00
            await asyncio.sleep(delay)
            load_gtfs_data()
        except Exception:
            logging.exception("load_gtfs_data failed")
            await asyncio.sleep(60)

async def lissy_worker():
    while True:
        try:
            delay = seconds_until_next_daily(hour=4, minute=0)
            await asyncio.sleep(delay)
            await cache_lissy()
        except Exception:
            logging.exception("cache_lissy failed")
            await asyncio.sleep(60)
