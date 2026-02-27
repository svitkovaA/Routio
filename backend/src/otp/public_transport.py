from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Tuple
from gql import gql
from models.route import OTPPublicQueryResponse, TripPattern
from routing_engine.routing_context import RoutingContext
from otp.otp_base import OTPBase

class OTPPublicTransport(OTPBase):
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
        # Base constructor
        super().__init__(context)

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
            parsed = await self._execute_query(
                self.QUERY,
                local_variables,
                OTPPublicQueryResponse.model_validate,
                fallback=None
            )

            if parsed is None:
                continue

            trip_patterns = parsed.trip.tripPatterns

            # Mark no trip patterns returned
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
        local_variables = deepcopy(self.__global_variables)
        local_variables["from"] = {
            "coordinates": {
                "latitude": origin[0],
                "longitude": origin[1]
            }
        }

        local_variables["to"] = {
            "coordinates": {
                "latitude": destination[0],
                "longitude": destination[1]
            }
        }

        local_variables["dateTime"] = time_cursor.isoformat()

        if allow_direct_foot:
            local_variables["modes"]["directMode"] =  "foot"

        return local_variables        
