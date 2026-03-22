"""
file: public_transport.py

OpenTripPlanner public transport client.
"""

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Tuple
from gql import gql
from models.route import OTPPublicQueryResponse, TripPattern
from routing_engine.routing_context import RoutingContext
from otp.otp_base import OTPBase

class OTPPublicTransport(OTPBase):
    """
    OTP client for public transport routing.
    """
    QUERY = gql("""
        query trip($from: Location!, $to: Location!, $dateTime: DateTime, $walkSpeed: Float, $maximumTransfers: Int, $pageCursor: String, $modes: Modes, $arriveBy: Boolean) {
            trip(
                from: $from
                to: $to
                dateTime: $dateTime
                walkSpeed: $walkSpeed
                maximumTransfers: $maximumTransfers
                pageCursor: $pageCursor
                modes: $modes
                arriveBy: $arriveBy
            ) {
                nextPageCursor
                tripPatterns {
                    aimedEndTime
                    legs {
                        mode
                        aimedStartTime
                        aimedEndTime
                        distance
                        duration
                        fromPlace {
                            latitude
                            longitude
                            name
                            quay {
                                id
                                name
                            }
                        }
                        toPlace {
                            latitude
                            longitude
                            name
                            quay {
                                id
                                name
                            }
                        }
                        line {
                            publicCode
                            name
                            id
                            authority {
                                name
                            }
                            presentation {
                                colour
                                textColour
                            }
                        }
                        serviceJourney {
                            quays {
                                id
                                name
                            }
                            passingTimes {
                                departure {
                                    time
                                }
                            }
                        }
                        pointsOnLink {
                            points
                        }
                    }
                }
            }
        }
    """)

    def __init__(self, context: RoutingContext):
        """
        Initializes the public transport OTP client.

        Args:
            context: Global routing context containing configuration
        """
        # Initialize base OTP client
        super().__init__(context)

        # Preconfigured global GraphQL variables reused for every request
        self.__global_variables: Dict[str, Any] = {
            "walkSpeed": self._ctx.data.walk_speed / 3.6,
            "maximumTransfers": self._ctx.data.max_transfers,
            "pageCursor": "",
            "modes": {
                "accessMode": "foot",
                "egressMode": "foot",
                "transportModes": [
                    {"transportMode": mode}
                    for mode in self._ctx.data.selected_modes
                ]
            },
            "arriveBy": self._ctx.data.arrive_by
        }

    async def execute(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        time_cursor: datetime,
        allow_direct_foot: bool = False
    ) -> List[TripPattern]:
        """
        Executes public transport routing query using OTP.

        Args:
            origin: Coordinates in format lat, lon of trip origin
            destination: Coordinates in format lat, lon of trip destination
            time_cursor: Representing departure or arrival time
            allow_direct_foot: If true, enables direct walking mode

        Returns:
            List of trip patterns returned by OTP
        """
        # Prepare local GraphQL variables for the request
        local_variables = self.__prepare_variables(
            origin,
            destination,
            time_cursor,
            allow_direct_foot=allow_direct_foot
        )
        attempt = 0
        trip_patterns = []
        
        # Number of retry if OTP returns no trip patterns
        while attempt < 10:
            # Execute GraphQL query
            parsed = await self._execute_query(
                self.QUERY,
                local_variables,
                OTPPublicQueryResponse.model_validate,
                fallback=None
            )

            # Abort if query failed
            if parsed is None:
                break

            trip_patterns = parsed.trip.tripPatterns

            # If no patterns returned, try next page
            if len(trip_patterns) == 0:
                local_variables["pageCursor"] = parsed.trip.nextPageCursor
                attempt += 1
            else:
                break

        return trip_patterns

    def __prepare_variables(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        time_cursor: datetime,
        allow_direct_foot: bool = False
    ) -> Dict[str, Any]:
        """
        Prepares GraphQL variable payload for OTP query.

        Args:
            origin: Coordinates in format lat, lon of trip origin
            destination: Coordinates in format lat, lon of trip destination
            time_cursor: Used for routing request
            allow_direct_foot: If true, enables direct walking mode

        Returns:
            Dictionary containing GraphQL query variables
        """
        # Copy global configuration template
        local_variables = deepcopy(self.__global_variables)

        # Add origin coordinates
        local_variables["from"] = {
            "coordinates": {
                "latitude": origin[0],
                "longitude": origin[1]
            }
        }

        # Add destination coordinates
        local_variables["to"] = {
            "coordinates": {
                "latitude": destination[0],
                "longitude": destination[1]
            }
        }

        # Set request time
        local_variables["dateTime"] = time_cursor.isoformat()

        # Optionally allow direct walking mode
        if allow_direct_foot:
            local_variables["modes"]["directMode"] =  "foot"

        return local_variables        

# End of file public_transport.py
