"""
file: workers.py

Background asynchronous workers for periodic data updates and maintenance tasks
"""

import asyncio
import logging
from typing import Awaitable, Callable
from services.public_transport_service.lissy import cache_lissy
from database.db import database
from services.gtfs_gbfs_service import load_gbfs_data, load_gtfs_data, vehicle_position
from datetime import datetime, timedelta
from config.worker import *

def seconds_until_next(
    hour: int,
    minute: int = 0,
    weekday: int | None = None
) -> float:
    """
    Calculates seconds until the next occurrence of a given time

    Args:
        hour: Target hour
        minute: Target minute
        weekday: Optional target weekday, if not provided scheduled daily
    
    Returns:
        Seconds until next occurrence
    """

    # Determines current time
    now = datetime.now()

    # Determines target time
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Daily workers
    if weekday is None:
        if target <= now:
            target += timedelta(days=1)

    # Weekly workers
    else:
        days_ahead = (weekday - now.weekday()) % 7

        if days_ahead == 0 and target <= now:
            days_ahead = 7

        target += timedelta(days=days_ahead)

    return (target - now).total_seconds()

async def run_sync(fn: Callable[[], None]) -> None:
    """
    Run a synchronous function without parameters in a thread

    Args:
        fn: Synchronous callable function
    """
    await asyncio.to_thread(fn)

async def run_periodic(task: Callable[[], Awaitable[None]], delay_fn: Callable[[], float], initial_load: bool):
    """
    Periodically executes an asynchronous task

    Args:
        task: Asynchronous function to execute
        delay_fn: Function returning delay before next execution
        initial_load: If true, run task immediately on server start
    """
    while True:
        # Execute before wait
        if not initial_load:
            await asyncio.sleep(delay_fn())

        # Task execution
        try:
            await task()
        except Exception:
            logging.exception(f"{task.__name__} failed")

        # Wait after execution
        if initial_load:
            await asyncio.sleep(delay_fn())

async def gtfs_worker():
    """
    Background task that refreshes GTFS static timetable data
    """
    await run_periodic(
        lambda: run_sync(load_gtfs_data),
        lambda: seconds_until_next(**GTFS_INTERVAL),
        initial_load=False
    )

async def gbfs_worker():
    """
    Background task that refreshes GBFS bike station data
    """
    await run_periodic(
        lambda: run_sync(load_gbfs_data),
        lambda: seconds_until_next(**GBFS_INTERVAL),
        initial_load=False
    )

async def database_worker():
    """
    Background task responsible for periodic database updates
    """
    await run_periodic(
        database,
        lambda: seconds_until_next(**DATABASE_INTERVAL),
        initial_load=True
    )

async def lissy_worker():
    """
    Background task that refreshes cached Lissy route shapes and delay data
    """
    await run_periodic(
        cache_lissy,
        lambda: seconds_until_next(**LISSY_INTERVAL),
        initial_load=False
    ) 

async def vehicle_position_worker():
    """
    Background worker that periodically updates vehicle position data
    """
    await run_periodic(
        vehicle_position,
        lambda: VEHICLE_POSITION_INTERVAL,
        initial_load=True
    )

# End of file workers.py
