"""
file: gtfs_enricher.py

Implements GTFSEnricher, responsible for enriching public transport legs using
static GTFS data.
"""

from service.gtfs_service import GTFSService
from models.route import TIME_DEPENDENT_MODES, TripPattern
from routers.public_transport.enrichers.enricher_base import EnricherBase

class GTFSEnricher(EnricherBase):
    """
    Enricher that augments public transport legs with static GTFS data.
    """
    def __init__(self):
        super().__init__()

        # Initialize GTFSService instance
        self.__service = GTFSService.get_instance()

    async def enrich(self, trip_pattern: TripPattern) -> None:
        """
        Enriches public transport legs in a trip pattern with alternative
        departures between stops, trip_id and route color information.

        Args:
            trip_pattern: Trip pattern to enrich
        """
        for leg in trip_pattern.legs:
            # Skip not time dependent legs
            if leg.mode not in TIME_DEPENDENT_MODES:
                continue

            # Add alternative departures to public transport legs
            if (leg.fromPlace and leg.fromPlace.quay and 
                leg.toPlace and leg.toPlace.quay and 
                leg.line
            ):
                # Retrieve departure options from GTFS service
                departures = self.__service.get_departures_via(
                    leg.line.authority["name"],
                    leg.fromPlace.quay.id.split(":", 1)[1], 
                    leg.toPlace.quay.id.split(":", 1)[1], 
                    leg.line.publicCode, 
                    leg.aimedStartTime
                )

                # Attach departure alternatives to leg
                leg.otherOptions = departures
                
                # Attach trip_id of selected departure when a matching departure is found
                if departures.currentIndex and departures.currentIndex >= 0:
                    leg.tripId = departures.departures[departures.currentIndex].tripId

            # Attach route color if available
            if leg.line and "colour" in leg.line.presentation:
                leg.color = f"#{leg.line.presentation["colour"]}"

# End of file gtfs_enricher.py
