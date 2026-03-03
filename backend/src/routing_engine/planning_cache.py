"""
file: planning_cache.py

Provides asynchronous route caching for the recursive planner.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Tuple
from models.route import RoutingMode, TripPattern, WaypointGroup

# Unique key identifying a routing request
CacheKey = Tuple[Tuple[str, ...], RoutingMode, datetime | None]

class PlanningCache():
    """
    Asynchronous cache for route planning results.
    """
    def __init__(self):
        # Mapping cache key to asyncio task
        self.__cache: Dict[CacheKey, asyncio.Task[List[TripPattern]]] = {}

    async def get_or_create_route(
        self,
        group: WaypointGroup,
        timestamp: datetime,
        route_fn: Callable[[], Coroutine[Any, Any, List[TripPattern]]]
    ) -> List[TripPattern]:
        """
        Returns cached route results or creates a new routing task

        Args:
            group: Waypoint group representing current segment
            timestamp: Temporal reference for routing
            route_fn: Asynchronous routing function to execute if needed

        Returns:
            List of TripPattern objects for the requested route
        """
        # Generate unique cache key identifying the routing request
        key = group.get_key(timestamp)

        # Create and store async routing task if route not cached yet
        if key not in self.__cache:
            self.__cache[key] = asyncio.create_task(route_fn())

        # Await cached or newly created routing task
        return await self.__cache[key]

# End of file planning_cache.py
