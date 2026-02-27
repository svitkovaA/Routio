from service.gtfs_service import GTFSService
from models.route import TIME_DEPENDENT_MODES, TripPattern
from routers.public_transport.enrichers.enricher_base import EnricherBase

class GTFSEnricher(EnricherBase):
    def __init__(self):
        super().__init__()
        self.__service = GTFSService.get_instance()

    async def enrich(self, trip_pattern: TripPattern) -> None:
        for leg in trip_pattern.legs:
            if leg.mode not in TIME_DEPENDENT_MODES:
                continue

            # Add alternative departure options to public transport legs
            if (leg.fromPlace and leg.fromPlace.quay and 
                leg.toPlace and leg.toPlace.quay and 
                leg.line
            ):
                departures = self.__service.get_departures_via(
                    leg.fromPlace.quay.id.split(":", 1)[1], 
                    leg.toPlace.quay.id.split(":", 1)[1], 
                    leg.line.publicCode, 
                    leg.aimedStartTime
                )
                leg.otherOptions = departures
                
                # Attach trip_id when a matching departure is found
                if departures.currentIndex and departures.currentIndex >= 0:
                    leg.tripId = departures.departures[departures.currentIndex].tripId

            # Add color to leg
            if leg.line:
                color = self.__service.get_color(leg.line.publicCode)
                if color:
                    leg.color = color
