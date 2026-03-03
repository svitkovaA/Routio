"""
file: lissy_enricher.py

Implements LissyEnricher, responsible for enriching public transport legs with
historical delay data and shape geometry.
"""

import asyncio
from datetime import date
from typing import Dict, List, Literal, Set, Tuple
import polyline                             # type: ignore[import-untyped]
from models.lissy import LissyShape
from service.lissy_service import LissyService
from models.route import Leg, TripPattern, TIME_DEPENDENT_MODES
from routers.public_transport.enrichers.enricher_base import EnricherBase

DelayResult = Tuple[Literal["delay"], Leg, Dict[str, int] | None]
ShapeResult = Tuple[Literal["shape"], Leg, Tuple[LissyShape, str] | None]

class LissyEnricher(EnricherBase):
    """
    Enricher that augments public transport legs with historical delays and
    shape geometry. Data are retrieved from LissyService and are applied in
    place to corresponding trip pattern legs.
    """
    def __init__(self, use_historical_delays: bool) -> None:
        """
        Initialize Lissy enricher.

        Args:
            use_historical_delays: Enables fetching historical delay data
        """
        super().__init__()

        # Create instance of Lissy service
        self.__service = LissyService.get_instance()

        # Store if fetching historical delays is enabled
        self.__use_historical_delays = use_historical_delays

    async def enrich(self, trip_pattern: TripPattern) -> None:
        """
        Enriches all public transport legs in a trip pattern.

        Args:
            trip_pattern: Trip pattern to enrich
        """
        delay_requests: List[Tuple[Leg, List[Tuple[int, str]], int]] = []
        shape_requests: List[Tuple[Leg, str, str]] = []

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
            
            # Extract line identifier and terminal stops
            name = leg.line.publicCode
            stops = f"{leg.serviceJourney.quays[0].name} -> {leg.serviceJourney.quays[-1].name}"

            # Prepare shape request
            shape_requests.append((leg, name, stops))

            # Store direction name
            leg.serviceJourney.direction = leg.serviceJourney.quays[-1].name
            
            # Maps stop_name to index within service journey
            quay_index_map = {quay.name: i for i, quay in enumerate(leg.serviceJourney.quays)}

            # Determine boarding and alighting stop indexes
            start_index = quay_index_map.get(leg.fromPlace.name if leg.fromPlace.name else "", -1)
            stop_index = quay_index_map.get(leg.toPlace.name if leg.toPlace.name else "", -1)

            # Validate stop range
            if start_index != -1 and stop_index != -1 and start_index <= stop_index:
                
                # Keep only intermediate stops
                leg.serviceJourney.quays = leg.serviceJourney.quays[start_index + 1:stop_index]

                # Fetch historical delays if enabled
                if self.__use_historical_delays:
                    # Find trip IDs corresponding to the departure time
                    trip_ids = self.__service.get_trip_id_by_time(
                        name, 
                        stops, 
                        leg.serviceJourney.passingTimes[0]["departure"].time
                    )

                    if trip_ids:
                        delay_requests.append((leg, trip_ids, start_index))

        results: List[ShapeResult | DelayResult] = await asyncio.gather(*[
            self.__delay_task(leg, trip_ids, index)
            for (leg, trip_ids, index) in delay_requests
        ], *[
            self.__shape_task(leg, trip_pattern.aimedEndTime.date(), name, stops)
            for (leg, name, stops) in shape_requests
        ])

        # Apply retrieved results
        for item in results:
            # Skip failed requests
            if item[2] is None:
                continue

            # Assign historical delays
            if item[0] == "delay":
                item[1].delays = item[2]
            # Assign shape and process geometry
            else:
                self.__process_shape_result(item[1], *item[2])
    
    async def __delay_task(self, leg: Leg, trip_ids: List[Tuple[int, str]], index: int) -> DelayResult:
        """
        Asynchronous task for retrieving historical delay data.

        Args:
            leg: Target leg
            trip_ids: Candidate trip ids
            index: Stop index for which delay is requested

        Returns:
            Tagged delay result tuple
        """
        delays = await self.__service.get_delays(trip_ids, index)
        return ("delay", leg, delays)

    async def __shape_task(self, leg: Leg, date: date, name: str, stops: str) -> ShapeResult:
        """
        Asynchronous task for retrieving route shape geometry.

        Args:
            leg: Target leg
            date: Service date
            name: Line identifier
            stops: Stop pair string

        Returns:
            Tagged shape result tuple
        """
        result = await self.__service.get_shape(date, name, stops)
        return ("shape", leg, result)

    @staticmethod
    def __process_shape_result(leg: Leg, shape: LissyShape, color: str) -> None:
        """
        Processes shape result and encodes polyline geometry.

        Args:
            leg: Target leg
            shape: Retrieved shape from Lissy
            color: Route color
        """
        # Retrieve color since route color is optional parameter in GTFS
        leg.color = color

        # Ensure valid stop references
        if not leg.fromPlace or not leg.toPlace:
            return
        
        # Determine relevant stop range
        stop_index_map: Dict[str, int] = {stop.stop_name: i for i, stop in enumerate(shape.stops)}
        from_idx = stop_index_map.get(leg.fromPlace.name if leg.fromPlace.name else "", -1)
        to_idx = stop_index_map.get(leg.toPlace.name if leg.toPlace.name else "", -1)

        if from_idx == -1 or to_idx == -1 or from_idx > to_idx:
            return

        # Collect active segment coordinates
        coords: List[Tuple[float, float]] = []
        zone_ids: Set[int] = set()

        for i in range(from_idx, to_idx):
            coords.extend(shape.coords[i])
            zone_ids.add(shape.stops[i].zone_id)

        # Collect previous, inactive, segment coordinates
        prev_coords: List[Tuple[float, float]] = []
        for i in range(from_idx):
            prev_coords.extend(shape.coords[i])

        # Collect next, inactive, segment coordinates
        next_coords: List[Tuple[float, float]] = []
        for i in range(to_idx, len(shape.coords)):
            next_coords.extend(shape.coords[i])

        # Encode inactive segments to polyline
        inactive_coords: List[str] = []
        if prev_coords:
            inactive_coords.append(polyline.encode(prev_coords))

        if next_coords:
            inactive_coords.append(polyline.encode(next_coords))

        # Encode active segment to polyline
        leg.pointsOnLink.points = [polyline.encode(coords)]
        leg.pointsOnLink.inactivePoints = inactive_coords

        zone_ids_list = list(zone_ids)
        zone_ids_list.sort()
        leg.zone_ids = zone_ids_list

# End of file lissy_enricher.py
