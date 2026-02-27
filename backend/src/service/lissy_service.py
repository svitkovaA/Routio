import asyncio
from dataclasses import dataclass
from datetime import date as d, timedelta, datetime
from typing import Dict, List, Tuple
from collections import OrderedDict
import httpx
from dateutil.relativedelta import relativedelta
from config.lissy_ben import DELAY_DATA_URL, DELAY_ROUTES_URL, DELAY_TRIPS_URL, LISSY_API_KEY, SHAPE_URL, SHAPES_URL
from models.lissy import LissyAvailableRoute, LissyDelayTrips, LissyRouteData, LissyShape, LissyShapes
from service.service_base import ServiceBase

@dataclass(frozen=True)
class _LissyState:
    # Maps route_short_name to route_color and trips
    shapes_cache: Dict[d, Dict[str, LissyShapes]]

    # Maps route_short_name to route_data
    routes_cache: Dict[str, Dict[str, LissyRouteData]]

class LissyService(ServiceBase[_LissyState]):
    # Size of the cache window
    CACHE_DAYS = 7

    # The maximum number of shape information in LRU cache
    MAX_SHAPE_CACHE_SIZE = 5000

    def __init__(self):
        super().__init__()
        self.__shape_lock = asyncio.Lock()

        # Maps shape_id to shape_data (LRU)
        self.__shape_detail_cache: OrderedDict[int, LissyShape] = OrderedDict()

        self.__client = httpx.AsyncClient(
            timeout=10, 
            headers={"Authorization": LISSY_API_KEY}
        )

    async def reload(self) -> None:
        print("Loading Lissy cache")
        new_state = await self.__cache()
        self._set_state(new_state)

    def get_trip_id_by_time(
        self,
        route_short_name: str,
        stops_label: str,
        dep_time: str
    ) -> int | None:
        """
        Finds a trip matching a given departure time for a specific route

        Args:
            route_short_name: The public code
            stops_label: Identifier representing origin->destination
            dep_time: The departure time

        Returns:
            Trip_id if the matching trip is found, None otherwise
        """
        state = self._get_state()

        # Normalize datetime ISO format to HH:MM:SS
        if "T" in dep_time:
            try:
                dep_time = datetime.fromisoformat(dep_time).strftime("%H:%M:%S")
            except ValueError:
                return None
            
        # Retrieve cached route data
        route_data = state.routes_cache.get(route_short_name)
        if not route_data:
            return None

        shape_data = route_data.get(stops_label)
        if not shape_data:
            return None

        trips_by_time = shape_data.trips_by_time
        if not trips_by_time:
            return None

        # Search for the closest matching trip within tolerance
        target_dt = datetime.strptime(dep_time, "%H:%M:%S")
        best_trip = None
        smallest_diff = timedelta(hours=24)
        tolerance_min = 5

        # Find closest trip to given time in the future
        for time_str, trip_id in trips_by_time.items():
            try:
                trip_dt = datetime.strptime(time_str, "%H:%M:%S")
            except ValueError:
                continue

            diff = (trip_dt - target_dt).total_seconds()

            # Accept only future departures within the tolerance window
            if 0 <= diff <= tolerance_min * 60 and diff < smallest_diff.total_seconds():
                smallest_diff = timedelta(seconds=diff)
                best_trip = trip_id

        # Return only one trip which is the closest to the given time in the future
        if best_trip:
            return best_trip
        
        return None

    async def get_delays(
        self,
        trip_id: int,
        index: int
    ) -> Dict[str, int] | None:
        """
        Retrieves historical delays for a specific trip and stop index
        
        Args:
            trip_id: The identifier of the trip
            index: Index of the stop within the trip for which the delay should be extracted

        Returns:
            A map with date strings and delay values
        """
        # Create a cache window in the format required by Lissy API
        cache_window_minus_month: List[str] = []
        for date in self.__get_cache_window(d.today()):
            dt = date - relativedelta(months=1)
            cache_window_minus_month.append(f"{dt.year}-{dt.month}-{dt.day}")

        dates_param = f'[["{cache_window_minus_month[3]}","{cache_window_minus_month[1]}"]]'

        # Fetch delay data for the given trip
        try:
            r = await self.__client.get(
                DELAY_DATA_URL, 
                params={"dates": dates_param, "trip_id": trip_id}
            )
            r.raise_for_status()
            data: Dict[str, Dict[str, Dict[str, int]]] = r.json()
            delays: Dict[str, int] = {}
            for date, delay in data.items():
                delay_data = delay[str(index)]
                value = list(delay_data.values())[0]
                delays[date] = value
            return delays
        except Exception:
            return None

    async def get_shapes_cached(
        self,
        date: d,
    ) -> Dict[str, LissyShapes]:
        """
        Returns cached route shape data for a given date

        Args:
            date: Date for which route shape data are requested
        
        Returns:
            A map containing route_short_name and shape_data
        """
        state = self._get_state()
        today = d.today()

        # Normalize date to fit into cache window
        date = self.__get_date(today, date)

        # Return cached shapes if available
        if date in state.shapes_cache:
            return state.shapes_cache[date]
        
        # Fetch and cache data if not already present
        shapes = await self.__get_shapes(date)
        if shapes:
            state.shapes_cache[date] = {
                shape.route_short_name: shape 
                for shape in shapes
            }
            return state.shapes_cache[date]

        return {}

    async def get_shape(
        self,
        shape_id: int
    ) -> LissyShape | None:
        """
        Retrieves detailed shape geometry for a given shape_id

        Args:
            shape_id:  Identifier of the shape whose geometry is requested

        Returns:
            Shape
        """
        async with self.__shape_lock:
            # Return shape from cache if available (LRU update)
            if shape_id in self.__shape_detail_cache:
                self.__shape_detail_cache.move_to_end(shape_id)
                return self.__shape_detail_cache[shape_id]
            
        # Fetch shape if not already present
        try:
            r = await self.__client.get(
                SHAPE_URL, 
                params={"shape_id": shape_id}
            )
            r.raise_for_status()
            data = LissyShape.model_validate(r.json())
        except Exception:
            return None

        async with self.__shape_lock:   
            # Store fetched shape in cache
            self.__shape_detail_cache[shape_id] = data
            self.__shape_detail_cache.move_to_end(shape_id)

            # Enforce maximum cache size (LRU eviction)
            if len(self.__shape_detail_cache) > self.MAX_SHAPE_CACHE_SIZE:
                self.__shape_detail_cache.popitem(last=False)
        return data

    async def __cache(self) -> _LissyState:
        shapes_cache: Dict[d, Dict[str, LissyShapes]] = {}
        routes_cache: Dict[str, Dict[str, LissyRouteData]] = {}

        # Determine the date window to cache
        cache_window = self.__get_cache_window(d.today())

        # Prepare async tasks for fetching shapes for each date    
        tasks = [
            self.__get_shapes(day) 
            for day in cache_window
        ]

        # Execute shape requests concurrently
        results = await asyncio.gather(*tasks)

        # Store shapes in cache indexed by date
        for day, shapes in zip(cache_window, results):
            if shapes:
                # Maps route short name to route_color and trips
                shapes_cache[day] = {
                    shape.route_short_name: shape 
                    for shape in shapes
                }

        parsed_routes = await self.__fetch_available_routes(cache_window)
        if parsed_routes:
            route_map = await self.__build_routes_map(
                parsed_routes, 
                cache_window
            )
            routes_cache.update(route_map)

        return _LissyState(
            shapes_cache=shapes_cache,
            routes_cache=routes_cache
        )

    @staticmethod
    def __get_cache_window(today: d) -> List[d]:
        """
        Docstring for get_cache_window
        
        Args:
            today: Reference date from which the cache window is computed

        Returns:
            List of dates in ISO format

        """
        return [ 
            (today - timedelta(days=i)) 
            for i in range(LissyService.CACHE_DAYS)
        ]
    
    async def __get_shapes(self, date: d) -> List[LissyShapes] | None:
        """
        Fetches route shapes for the given date
        
        Args:
            date: Date for which route shapes should be retrieved

        Returns:
            A list of route shapes if success, None otherwise
        """
        try:
            api_date = f"{date.year}-{date.month - 1}-{date.day}"
            r = await self.__client.get(SHAPES_URL, params={"date": api_date})
            r.raise_for_status()
            data = [
                LissyShapes.model_validate(obj)
                for obj in r.json()
            ]
        except Exception:
            return None
        return data

    async def __fetch_available_routes(
        self, 
        cache_window: List[d]
    ) -> List[LissyAvailableRoute]:
        # Months in lissy are in format 0-11
        cache_window_minus_month: List[str] = []
        for date in cache_window:
            dt = date - relativedelta(months=1)
            cache_window_minus_month.append(f"{dt.year}-{dt.month}-{dt.day}")

        # Try to fetch routes for which the delays are available
        try:
            # Example of dates_param format '[["2025-9-8","2025-9-10"]]'
            dates_param = f'[["{cache_window_minus_month[3]}","{cache_window_minus_month[1]}"]]'
            r = await self.__client.get(
                DELAY_ROUTES_URL,
                params={"dates": dates_param}
            )
            r.raise_for_status()
            parsed = [
                LissyAvailableRoute.model_validate(obj)
                for obj in r.json()
            ]    
            return parsed
        except Exception:
            return []

    async def __build_routes_map(
        self,
        routes_list: List[LissyAvailableRoute],
        cache_window: List[d]
    ) -> Dict[str, Dict[str, LissyRouteData]]:
        """
        Builds and caches stop_label to shape_id, stopOrder and trips_by_time map

        Args:
            routes_list: List of available routes returned by Lissy API
            cache_window: List of dates in ISO format
        """
        routes_cache: Dict[str, Dict[str, LissyRouteData]] = {}

        # Build date range required for the delay API
        start_date = cache_window[3] - relativedelta(months=1)
        end_date = cache_window[1] - relativedelta(months=1)
        start_str = f"{start_date.year}-{start_date.month}-{start_date.day}"
        end_str = f"{end_date.year}-{end_date.month}-{end_date.day}"
        dates = f'[["{start_str}","{end_str}"]]'

        # Fetch route data concurrently
        results = await asyncio.gather(*[
            self.__fetch_route_data(route, dates)
            for route in routes_list
        ])

         # Store non empty data to cache
        for short_name, route_data in results:
            if route_data:
                routes_cache[short_name] = route_data

        return routes_cache

    async def __fetch_route_data(
        self,
        route: LissyAvailableRoute,
        dates: str
    ) -> Tuple[str, Dict[str, LissyRouteData]]:
        """
        Fetch trip data for delay from Lissy API
        
        Args:
            route: Route descriptor
        
        Returns:
            A tuple, including route_short_name and route_data
        """

        route_id = route.id
        short_name = route.route_short_name

        # Fetch available trips for the selected date range
        try:
            # Returns shape id, stops and trips
            r = await self.__client.get(
                DELAY_TRIPS_URL, 
                params={ 
                    "dates": dates,
                    "route_id": route_id, 
                    "fullStopOrder": True
                }
            )
            r.raise_for_status()
            data = [
                LissyDelayTrips.model_validate(obj)
                for obj in r.json()
            ]

            route_data: Dict[str, LissyRouteData] = {}
            for shape in data:
                shape_id = shape.shape_id
                stops_label = shape.stops or f"shape_{shape_id}"
                stop_order = shape.stopOrder
                trips = shape.trips

                # Maps departure time to trip_id
                trips_by_time: dict[str, int] = {}
                for trip in trips:
                    dep_time = trip.dep_time
                    trip_id = trip.id

                    if dep_time is not None and trip_id is not None:
                        trips_by_time[dep_time] = trip_id

                # From stop label get information
                route_data[stops_label] = LissyRouteData(
                    shape_id=shape_id,
                    stopOrder=stop_order,
                    trips_by_time=trips_by_time
                )

            return short_name, route_data
        
        except Exception:
            return short_name, {}

    @staticmethod
    def __get_date(today: d, date: d) -> d:
        """
        Normalizes a date to fit within the cache window
        
        Args:
            today: The reference date
            date: Date to be normalized to the cache window
        
        Returns:
            A date that is less than or equal to the reference date and aligned
            with the cache window size
        """
        while date > today:
            date -= timedelta(days=LissyService.CACHE_DAYS)
        return date
