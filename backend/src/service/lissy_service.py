"""
file: lissy_service.py

This file implements an asynchronous service for integrating data retrieved
from Lissy API into application. The data includes shapes geometries and
historical delays for the last 7 day window.
"""

import asyncio
import re
import json
from dataclasses import dataclass
from datetime import date as d, timedelta, datetime
from pathlib import Path
import shutil
from typing import Dict, List, Tuple
from collections import OrderedDict
import httpx
from config.datasets import LISSY_DELAY_CACHE_PATH
from config.lissy_ben import (
    DELAY_DATA_URL,
    DELAY_ROUTES_URL,
    DELAY_TRIPS_URL,
    LISSY_API_KEY,
    SHAPE_URL,
    SHAPES_ROUTES_URL
)
from models.lissy import (
    LissyAvailableRoute,
    LissyDelayTrips,
    LissyDelayRoutes,
    LissyShape,
    LissyShapesRoutes
)
from service.service_base import ServiceBase

@dataclass(frozen=True)
class _LissyState:
    # Maps date to route_short_name to (route_short_name, route_color, trips)
    shapes_cache: Dict[d, Dict[str, LissyShapesRoutes]]

class LissyService(ServiceBase[_LissyState]):
    """
    Service responsible for retrieving, caching and serving Lissy API data.
    """
    # The number of past days to cache shapes
    SHAPES_CACHE_DAYS = 7

    # The maximum size of LRU shape cache
    MAX_SHAPE_CACHE_SIZE = 5000

    # The number of past days to cache historical delays
    DELAYS_CACHE_DAYS = 7

    def __init__(self):
        super().__init__()

        # Asynchronous lock protecting LRU shape cache
        self.__shape_cache_lock = asyncio.Lock()

        # Maps shape_id to shape_data (in LRU)
        self.__shape_detail_cache: OrderedDict[int, LissyShape] = OrderedDict()

        # Asynchronous HTTP client for Lissy API
        self.__client = httpx.AsyncClient(
            timeout=10, 
            headers={"Authorization": LISSY_API_KEY}
        )

        # Local filesystem cache directory
        self.__cache_dir = Path(LISSY_DELAY_CACHE_PATH)
        self.__cache_dir.mkdir(parents=True, exist_ok=True)

    async def reload(self) -> None:
        """
        On reload updates Lissy data and replaces the internal cache state.
        """
        print("Loading Lissy cache")
        
        new_state = await self.__load_and_cache_state()
        self._set_state(new_state)
        
    # Caching data methods
    async def __load_and_cache_state(self) -> _LissyState:
        """
        Builds a Lissy service state including shape and historical delays data.

        Returns:
            Initialized internal Lissy state
        """
        # Maps date to (route_short_name, shape)
        shapes_cache: Dict[d, Dict[str, LissyShapesRoutes]] = {}

        # Determine the date window to cache shapes
        cache_window = self.__get_cache_window(d.today())

        # Prepare asynchronous tasks for fetching shapes 
        tasks = [
            self.__fetch_shapes_routes(day) 
            for day in cache_window
        ]

        # Execute shape requests concurrently
        results = await asyncio.gather(*tasks)

        # Store fetched shapes in cache indexed by date and route_short_name
        for day, shapes in zip(cache_window, results):
            if shapes:
                # Index shapes by route_short_name
                shapes_cache[day] = {
                    shape.route_short_name: shape 
                    for shape in shapes
                }

        # Fetch delay routes
        dates_to_delay_routes_map = await self.__get_delay_routes()

        # Build delay trip cache concurrently per date
        await asyncio.gather(*[
            self.__build_delay_routes_cache_for_date(
                routes,
                date
            )
            for date, routes in dates_to_delay_routes_map.items()
        ])

        return _LissyState(shapes_cache=shapes_cache)

    @staticmethod
    def __get_cache_window(today: d) -> List[d]:
        """
        Retrieve date window for shapes caching.
        
        Args:
            today: Reference date

        Returns:
            List of dates to be cached including today and previous SHAPES_CACHE_DAYS - 1

        """
        # Generate sliding window of past dates
        return [ 
            (today - timedelta(days=i)) 
            for i in range(LissyService.SHAPES_CACHE_DAYS)
        ]
    
    async def __get_delay_routes(self) -> Dict[str, List[LissyAvailableRoute]]:
        """
        Retrieves available routes for which delay data exist.

        Returns:
            Mapping date to list of delay routes
        """
        cache_dates: List[str] = []
        today = d.today()

        # Build list of last DELAYS_CACHE_DAYS days excluding today
        for i in range(1, self.DELAYS_CACHE_DAYS + 1):
            cache_day = today - timedelta(days=i)
            cache_dates.append(f"{cache_day.year}-{cache_day.month - 1}-{cache_day.day}")

        # Remove old directories
        for dir in self.__cache_dir.iterdir():
            if dir.is_dir() and dir.name not in cache_dates:
                shutil.rmtree(dir)
        
        # Create new directories
        unique_cache_dates: List[str] = []
        for date in cache_dates:
            date_dir = self.__cache_dir / date
            if not date_dir.exists():
                unique_cache_dates.append(date)

        # Fetch delay routes concurrently for all unique dates
        results = await asyncio.gather(*[
            self.__fetch_delay_routes(date)
            for date in unique_cache_dates
        ])

        # Maps date to available routes
        return {
            date: result
            for date, result in zip(unique_cache_dates, results)
        }
    
    async def __build_delay_routes_cache_for_date(
        self,
        routes: List[LissyAvailableRoute],
        date: str
    ) -> None:
        """
        Builds and caches retrieved delay routes.

        Args:
            routes: List of available delay routes
            date: Date to retrieve data
        """
        # Fetch delay trip data per date
        for route in routes:
            await self.__fetch_delay_trips(route, date)

    def __build_delay_routes_map(
        self,
        delay_trips: List[LissyDelayTrips],
        dir_path: Path
    ) -> None:
        """
        Transforms a list delay trips into an internally used lookup structure
        for caching.

        Args:
            delay_trips: List of retrieved delay trips
            dir_path: Path to cache directory
        """
        dir_path.mkdir(parents=True, exist_ok=True)

        for delay_trip in delay_trips:
            shape_id = delay_trip.shape_id
            stops_label = delay_trip.stops or f"shape_{shape_id}"
            trips = delay_trip.trips

            # Maps departure_time to trip_id
            trips_by_time: dict[str, int] = {}

            for trip in trips:
                dep_time = trip.dep_time
                trip_id = trip.id

                # Store only valid trip records
                if dep_time is not None and trip_id is not None:
                    trips_by_time[dep_time] = trip_id
            
            # Store the delay route representation
            file_path = dir_path / f"{self._hash_label(stops_label)}.json"
            with open(file_path, "w") as f:
                json.dump(
                    LissyDelayRoutes(
                        shape_id=shape_id,
                        trips_by_time=trips_by_time
                    ).model_dump(),
                    f,
                    indent=2,
                    ensure_ascii=False
                )

    # External API fetches
    async def __fetch_shapes_routes(self, date: d) -> List[LissyShapesRoutes] | None:
        """
        Fetches route shapes for the given date.
        
        Args:
            date: Date for which route shapes should be retrieved

        Returns:
            A list of route shapes on success, None otherwise
        """
        try:
            # Convert date to API format (months are in format 0-11)
            api_date = f"{date.year}-{date.month - 1}-{date.day}"

            r = await self.__client.get(SHAPES_ROUTES_URL, params={"date": api_date})
            r.raise_for_status()

            # Validate and deserialize response objects
            data = [
                LissyShapesRoutes.model_validate(obj)
                for obj in r.json()
            ]

        except Exception as e:
            print(e)
            return None

        return data

    async def __fetch_delay_routes(
        self,
        date: str
    ) -> List[LissyAvailableRoute]:
        """
        Fetches available routes for which delay data exist.

        Args:
            date: Date string already in API format
        
        Returns:
            List of available delay routes
        """
        # Try to fetch routes for which the delays are available
        try:
            # API estimates dates in nested interval format 
            dates_param = f'[["{date}","{date}"]]'
            r = await self.__client.get(
                DELAY_ROUTES_URL,
                params={"dates": dates_param}
            )
            r.raise_for_status()

            # Validate and deserialize response objects
            parsed = [
                LissyAvailableRoute.model_validate(obj)
                for obj in r.json()
            ]
            return parsed
        
        except Exception as e:
            print(e)
            return []

    async def __fetch_delay_trips(
        self,
        route: LissyAvailableRoute,
        date: str
    ) -> None:
        """
        Fetches available delay route trips for the given dates and transforms
        them into an internal cache structure.
        
        Args:
            route: Route descriptor
            date: Date already in API format
        """
        # Build date range required for the delay API
        date_range = f'[["{date}","{date}"]]'

        route_id = route.id
        route_short_name = route.route_short_name

        # Fetch available delay trip data for given route and date
        try:
            r = await self.__client.get(
                DELAY_TRIPS_URL, 
                params={ 
                    "dates": date_range,
                    "route_id": route_id
                }
            )
            r.raise_for_status()

            # Deserialize API response
            raw_delay_trips = [
                LissyDelayTrips.model_validate(obj)
                for obj in r.json()
            ]

            # Transform response into internal cache model
            self.__build_delay_routes_map(
                raw_delay_trips,
                self.__cache_dir / date / route_short_name
            )
                    
        except Exception as e:
            print(e)

    async def __fetch_shape(
        self,
        shape_id: int
    ) -> LissyShape | None:
        """
        Retrieves detailed shape geometry for a given shape_id

        Args:
            shape_id: Identifier of the shape whose geometry is requested

        Returns:
            Shape object
        """     
        # Request shape geometry
        try:
            r = await self.__client.get(
                SHAPE_URL, 
                params={"shape_id": shape_id}
            )
            r.raise_for_status()

            # Validate and parse response
            data = LissyShape.model_validate(r.json())

        except Exception as e:
            print(e)
            return None

        return data

    # Enrichment methods
    def get_trip_id_by_time(
        self,
        route_short_name: str,
        stops_label: str,
        departure_time: str
    ) -> List[Tuple[int, str]]:
        """
        Finds trip ids matching a given departure time.

        Args:
            route_short_name: The public route code
            stops_label: Identifier representing origin -> destination
            departure_time: The departure time

        Returns:
            List of (trip_id, date string)
        """
        # Normalize datetime in ISO format to HH:MM:SS
        if "T" in departure_time:
            try:
                departure_time = datetime.fromisoformat(departure_time).strftime("%H:%M:%S")
            except ValueError:
                return []

        # Determine relevant cache dates based on weekday matching
        dates = self.__get_delay_cache_dates()

        # Parse target departure time
        target_departure_time = datetime.strptime(departure_time, "%H:%M:%S")

        # Tolerance window in minutes
        tolerance_min = 5

        # Collected (trip_id, date)
        trip_ids: List[Tuple[int, str]] = []

        for date in dates:
            # Build path to cached delay file
            delay_route_dir = self.__cache_dir / date
            route_dir = delay_route_dir / route_short_name
            stops_file = route_dir / f"{self._hash_label(stops_label)}.json"

            # Skip if cache file does not exist
            if not stops_file.exists():
                continue

            # Load cached delay trips
            with open(stops_file) as f:
                delay_trips = json.load(f)

            trips_by_time = delay_trips["trips_by_time"]

            # Track closest future departure
            best_trip = None
            smallest_diff = timedelta(hours=24)

            # Find closest trip to the given time in the future within tolerance
            for time_str, trip_id in trips_by_time.items():
                try:
                    trip_dt = datetime.strptime(time_str, "%H:%M:%S")
                except ValueError:
                    continue

                # Compute difference in seconds
                diff = (trip_dt - target_departure_time).total_seconds()

                # Accept only future departures within tolerance
                if 0 <= diff <= tolerance_min * 60 and diff < smallest_diff.total_seconds():
                    smallest_diff = timedelta(seconds=diff)
                    best_trip = trip_id

            # Store only one closest trip to the given time in the future
            if best_trip:
                trip_ids.append((best_trip, date))

        return trip_ids

    def __get_delay_cache_dates(self) -> List[str]:
        """
        Selects cached dates.

        Returns:
            List of date in API format
        """
        # Reference date
        today = d.today()

        # Build sliding of previous days
        window = [
            today - timedelta(days=i)
            for i in range(1, self.DELAYS_CACHE_DAYS + 1)
        ]

        # Convert window to API format
        return [
            f"{date.year}-{date.month - 1}-{date.day}"
            for date in window
        ]
    
    @staticmethod
    def __convert_month(date: str) -> str:
        """
        Increments the month value in a date string for correct date
        visualisation on frontend.

        Args:
            date: Date in format YYYY-M-D or YYYY-MM-DD

        Returns:
            Date string with the month increased by 1
        """
        def repl(match: re.Match[str]) -> str:
            year = match.group(1)
            month = int(match.group(2)) + 1
            day = match.group(3)

            # Construct updated date string
            return f"{year}-{month}-{day}"

        # Replace month value
        return re.sub(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', repl, date)

    async def get_delays(
        self,
        trip_ids: List[Tuple[int, str]],
        index: int
    ) -> Dict[str, int] | None:
        """
        Retrieves historical delays for a specific trip ids and stop index.
        
        Args:
            trip_ids: List of (trip_id, date)
            index: Stop index within the trip

        Returns:
            Mapping date string to delay value
        """
        # Maps date to delay
        delays: Dict[str, int] = {}
        
        for trip_id, date in trip_ids:
            # Build API date parameter
            dates_param = f'[["{date}","{date}"]]'

            # Fetch delay data for the given trip
            try:
                r = await self.__client.get(
                    DELAY_DATA_URL, 
                    params={"dates": dates_param, "trip_id": trip_id}
                )
                r.raise_for_status()

                # Expected json format: { date: { stop_index: { timestamp: delay_value }}}
                data: Dict[str, Dict[str, Dict[str, int]]] = r.json()
                for date_res, delay in data.items():
                    # Extract delay data for requested stop index
                    delay_data = delay[str(index)]

                    # Extract first available delay value
                    value = list(delay_data.values())[0]

                    # Store result in output map
                    delays[self.__convert_month(date_res)] = value

            except Exception as e:
                print(e)
                continue
            
        # Return None if no delay data found
        return delays if delays else None

    async def get_shape(
        self,
        date: d,
        route_short_name: str,
        stops: str
    ) -> Tuple[LissyShape, str] | None:
        """
        Retrieves detailed shape geometry for a route and stop sequence.

        Args:
            date: Reference date
            route_short_name: The public route code
            stops: Stop sequence identifier

        Returns:
            Tuple (shape, hexadecimal color)
        """
        # Retrieve cached shape route data for the given date
        shape_route_info_map = await self.__get_shapes_cached(date)
        shape_route_info = shape_route_info_map.get(route_short_name)

        # Return if route is not available for the given date
        if not shape_route_info:
            return None
        
        shape_id = None

        # Find matching shape_id based on stops sequence
        for trip in shape_route_info.trips:
            if trip.stops == stops:
                shape_id = trip.shape_id
                break
        
        # Return if no matching shape_id was found
        if not shape_id:
            return None
        
         # Prepare route color in hexadecimal format
        color = f"#{shape_route_info.route_color}"
        
        async with self.__shape_cache_lock:
            # Return shape from cache if available and update LRU order
            if shape_id in self.__shape_detail_cache:
                self.__shape_detail_cache.move_to_end(shape_id)
                return self.__shape_detail_cache[shape_id], color
        
        # Fetch shape geometry from external source if not cached
        shape = await self.__fetch_shape(shape_id)

        # Return if fetching shape failed
        if not shape:
            return None
        
        async with self.__shape_cache_lock:   
            # Store fetched shape in cache
            self.__shape_detail_cache[shape_id] = shape
            self.__shape_detail_cache.move_to_end(shape_id)

            # Remove oldest cached shape if cache size limit is exceeded
            if len(self.__shape_detail_cache) > self.MAX_SHAPE_CACHE_SIZE:
                self.__shape_detail_cache.popitem(last=False)
        
        return shape, color

    async def __get_shapes_cached(
        self,
        date: d,
    ) -> Dict[str, LissyShapesRoutes]:
        """
        Returns cached shape data for a given date. If data are not available,
        they are fetched and stored into cache.

        Args:
            date: Date for which route shape data are requested
        
        Returns:
            Mapping route_short_name to shape data
        """
        state = self._get_state()
        today = d.today()

        # Normalize date to fit into cache window
        date = self.__normalize_date_to_cache_window(today, date)

        # Return cached shapes if already available
        if date in state.shapes_cache:
            return state.shapes_cache[date]
        
        # Fetch and cache data if not already present
        shapes = await self.__fetch_shapes_routes(date)
        if shapes:
            # Store shapes mapped by route_short_name
            state.shapes_cache[date] = {
                shape.route_short_name: shape 
                for shape in shapes
            }
            return state.shapes_cache[date]

        return {}

    @staticmethod
    def __normalize_date_to_cache_window(today: d, date: d) -> d:
        """
        Normalizes a future date to fit within the cache window.
        
        Args:
            today: The reference date
            date: Date to be normalized to the cache window
        
        Returns:
            A date that is less than or equal to the reference date and aligned
            with the cache window size
        """
        while date > today:
            date -= timedelta(days=LissyService.SHAPES_CACHE_DAYS)

        return date

# End of file lissy_service.py
