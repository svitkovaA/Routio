import asyncio
from typing import Dict, List, Set, Tuple
import polyline                             # type: ignore[import-untyped]
from models.lissy import LissyShape, LissyShapes
from service.lissy_service import LissyService
from models.route import Leg, TripPattern, TIME_DEPENDENT_MODES
from routers.public_transport.enrichers.enricher_base import EnricherBase

class LissyEnricher(EnricherBase):
    def __init__(self) -> None:
        super().__init__()
        self.__service = LissyService.get_instance()

    async def enrich(self, trip_pattern: TripPattern) -> None:
        delay_requests: List[Tuple[Leg, int, int]] = []

        # Load cached route shapes for the given date
        shape_by_route = await self.__service.get_shapes_cached(
            trip_pattern.aimedEndTime.date()
        )

        shape_id_to_data = await self.__get_shape_data_map(
            trip_pattern,
            shape_by_route
        )

        for leg in trip_pattern.legs:
            # For public transport
            if (
                leg.mode not in TIME_DEPENDENT_MODES
                or not leg.line
                or not leg.serviceJourney
                or not leg.fromPlace
                or not leg.toPlace
            ):
                continue
            
            name = leg.line.publicCode
            stops = f"{leg.serviceJourney.quays[0].name} -> {leg.serviceJourney.quays[-1].name}"
            shape = shape_by_route.get(name)
            leg.serviceJourney.direction = leg.serviceJourney.quays[-1].name
            
            # Build stop_name to index map
            quay_index_map = {quay.name: i for i, quay in enumerate(leg.serviceJourney.quays)}

            # Find leg start and stop stop_name indexes
            start_index = quay_index_map.get(leg.fromPlace.name if leg.fromPlace.name else "", -1)
            stop_index = quay_index_map.get(leg.toPlace.name if leg.toPlace.name else "", -1)

            # Valid indexes found
            if start_index != -1 and stop_index != -1 and start_index <= stop_index:
                leg.serviceJourney.quays = leg.serviceJourney.quays[start_index + 1:stop_index]
                # Search trip id in cache, if delays available
                trip_id = self.__service.get_trip_id_by_time(
                    name, 
                    stops, 
                    leg.serviceJourney.passingTimes[0]["departure"].time
                )

                if trip_id:
                    delay_requests.append((leg, trip_id, start_index))

            if shape is None:
                continue

            leg.color = f"#{shape.route_color}"

            # Find shape_id for given stops
            shapeID = next((trip.shape_id for trip in shape.trips if trip.stops == stops), None)
            if shapeID is None:
                continue

            # Retrieve shape_data by id
            shape_by_ID = shape_id_to_data.get(shapeID)
            if shape_by_ID is None:
                continue

            # Find start and stop indexes in shape_data
            stop_index_map: Dict[str, int] = {stop.stop_name: i for i, stop in enumerate(shape_by_ID.stops)}
            from_idx = stop_index_map.get(leg.fromPlace.name if leg.fromPlace.name else "", -1)
            to_idx = stop_index_map.get(leg.toPlace.name if leg.toPlace.name else "", -1)
            if from_idx == -1 or to_idx == -1 or from_idx > to_idx:
                continue

            # Concat shapes in given stop range
            coords: List[Tuple[float, float]] = []
            for i in range(from_idx, to_idx):
                coords.extend(shape_by_ID.coords[i])

            # Encode coordinates to polyline
            leg.pointsOnLink.points = polyline.encode(coords)

        delay_results = await asyncio.gather(*[
            self.__service.get_delays(trip_id, index)
            for (_, trip_id, index) in delay_requests
        ])

        for (leg, _, _), delays in zip(delay_requests, delay_results):
            if delays:
                leg.delays = delays

    async def __get_shape_data_map(
        self,
        trip_pattern: TripPattern,
        shape_by_route: Dict[str, LissyShapes]
    ) -> Dict[int, LissyShape]:
        # Create list of the required shape ids
        needed_shape_ids: Set[int] = set()
        for leg in trip_pattern.legs:
            # For public transport modes
            if leg.mode in TIME_DEPENDENT_MODES:
                shape: LissyShapes | None = None
                stops = ""

                # Retrieve shape by public_code from cache
                if leg.line:
                    name = leg.line.publicCode
                    shape = shape_by_route.get(name)

                # Create stop_label
                if leg.serviceJourney:
                    stops = f"{leg.serviceJourney.quays[0].name} -> {leg.serviceJourney.quays[-1].name}"
                
                # Add shape_id to list of the required shape ids
                if shape:
                    for trip in shape.trips:
                        if trip.stops == stops:
                            needed_shape_ids.add(trip.shape_id)
        
        shape_data_list = await asyncio.gather(*[
            self.__service.get_shape(shape_id)
            for shape_id in needed_shape_ids
        ])

        return {
            shape_id: data
            for shape_id, data in zip(needed_shape_ids, shape_data_list)
            if data
        }
