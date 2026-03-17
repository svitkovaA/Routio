"""
file: workers.py

Background asynchronous workers for periodic data updates and maintenance tasks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Type
from service.prediction_service import PredictionService
from service.database_service import DatabaseService
from service.population_service import PopulationService
from service.service_base import ServiceBase
from service.gtfs_rt_service import GTFSRTService
from service.gbfs_service import GBFSService
from service.lissy_service import LissyService
from service.gtfs_service import GTFSService
from config.worker import *

async def _safe_reload(service: Type[ServiceBase[Any]]):
    """
    Reload a service instance with error handling.
    """
    try:
        await service.get_instance().reload()
    except Exception:
        logging.exception(f"Initial {service.__name__} failed")

async def load_initial_data():
    """
    Load all core services concurrently on application startup.
    """
    await asyncio.gather(
        _safe_reload(GTFSService),
        _safe_reload(GBFSService),
        _safe_reload(LissyService),
        _safe_reload(PopulationService),
        _safe_reload(DatabaseService)
    )
    await asyncio.gather(
        _safe_reload(GTFSRTService),
        _safe_reload(PredictionService)
    )

def seconds_until_next(
    hour: int,
    minute: int = 0,
    weekday: int | None = None
) -> float:
    """
    Calculate seconds until the next scheduled occurrence.

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

    # Daily scheduling
    if weekday is None:
        if target <= now:
            # Move to next day
            target += timedelta(days=1)

    # Weekly scheduling
    else:
        days_ahead = (weekday - now.weekday()) % 7

        if days_ahead == 0 and target <= now:
            # Move to next week
            days_ahead = 7

        target += timedelta(days=days_ahead)

    return (target - now).total_seconds()

def seconds_until_next_10min_offset(offset: int = 1) -> float:
    """
    Calculate seconds until next (10 minute interval + offset).

    Args:
        offset: offset in minutes
    """
    now = datetime.now()

    # Next 10-minute boundary
    next_minute = ((now.minute // 10) + 1) * 10 + offset

    target = now.replace(second=0, microsecond=0)

    if next_minute >= 60:
        target = target.replace(minute=offset) + timedelta(hours=1)
    else:
        target = target.replace(minute=next_minute)

    return (target - now).total_seconds()

async def run_periodic(task: Callable[[], Awaitable[None]], delay_fn: Callable[[], float], initial_load: bool):
    """
    Execute an asynchronous task periodically.

    Args:
        task: Asynchronous function to execute
        delay_fn: Function returning delay before next execution
        initial_load: If true, run task immediately on server start
    """
    while True:
        # Wait before execution if not initial load
        if not initial_load:
            await asyncio.sleep(delay_fn())

        # Execute scheduled task
        try:
            await task()
        except Exception:
            logging.exception(f"{task.__name__} failed")

        # Wait after execution if initial load was done
        if initial_load:
            await asyncio.sleep(delay_fn())

async def gtfs_worker():
    """
    Periodic worker for updating GTFS data.
    """
    await run_periodic(
        GTFSService.get_instance().reload,
        lambda: seconds_until_next(**GTFS_INTERVAL),
        initial_load=False
    )

async def gbfs_worker():
    """
    Periodic worker for updating GBFS data.
    """
    await run_periodic(
        GBFSService.get_instance().reload,
        lambda: seconds_until_next(**GBFS_INTERVAL),
        initial_load=False
    )

async def database_worker():
    """
    Periodic worker for updating database.
    """
    await run_periodic(
        DatabaseService.get_instance().reload,
        lambda: seconds_until_next_10min_offset(1),
        initial_load=True
    )

async def lissy_worker():
    """
    Periodic worker for updating data retrieved from Lissy.
    """
    await run_periodic(
        LissyService.get_instance().reload,
        lambda: seconds_until_next(**LISSY_INTERVAL),
        initial_load=False
    )

async def gtfs_rt_worker():
    """
    Periodic worker for updating GTFS-RT data.
    """
    await run_periodic(
        GTFSRTService.get_instance().reload,
        lambda: VEHICLE_POSITION_INTERVAL,
        initial_load=True
    )

# End of file workers.py
