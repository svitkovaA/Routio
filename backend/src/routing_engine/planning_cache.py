import asyncio
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Tuple
from models.route import RoutingMode, TripPattern, WaypointGroup

CacheKey = Tuple[Tuple[str, ...], RoutingMode, datetime | None]

class PlanningCache():
    def __init__(self):
        self.__cache: Dict[CacheKey, asyncio.Task[List[TripPattern]]] = {}

    async def get_or_create_route(
        self,
        group: WaypointGroup,
        timestamp: datetime,
        route_fn: Callable[[], Coroutine[Any, Any, List[TripPattern]]]
    ) -> List[TripPattern]:
        # Generate unique cache key for routing request
        key = group.get_key(timestamp)

        # Create and store async task if route not cached yet
        if key not in self.__cache:
            self.__cache[key] = asyncio.create_task(route_fn())

        # Await cached or newly created routing task
        return await self.__cache[key]

