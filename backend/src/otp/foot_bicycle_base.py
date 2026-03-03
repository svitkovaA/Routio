"""
file: foot_bicycle_base.py

Shared OpenTripPlanner client base for direct foot and bicycle routing.
"""

from abc import ABC
from gql import gql
from typing import Any, Dict, List, Literal, Tuple, final
from models.route import TripPattern
from models.route import OTPPublicQueryResponse
from otp.otp_base import OTPBase

class OTPFootBicycleBase(OTPBase, ABC):
    """
    Abstract base class for direct foot and bicycle OTP routing.
    """
    QUERY = gql("""
        query trip($from: Location!, $to: Location!, $modes: Modes, $walkSpeed: Float, $bikeSpeed: Float, $arriveBy: Boolean) {
            trip(
                from: $from
                to: $to
                modes: $modes
                walkSpeed: $walkSpeed
                bikeSpeed: $bikeSpeed
                arriveBy: $arriveBy
            ) {
                tripPatterns {
                    aimedEndTime
                    legs {
                        fromPlace {
                            latitude
                            longitude
                        }
                        toPlace {
                            latitude
                            longitude
                        }
                        mode
                        aimedStartTime
                        aimedEndTime
                        distance
                        duration
                        pointsOnLink {
                            points
                        }
                    }
                }
            }
        }
    """)

    @final
    async def _base_execute(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: Literal["foot", "bicycle"],
        mode_speed: float
    ) -> List[TripPattern]:
        """
        Executes direct routing query for foot or bicycle mode.

        Args:
            origin: Coordinates in format lat, lon of starting point
            destination: Coordinates in format lat, lon of destination
            mode: Transport mode
            mode_speed: Speed for selected mode

        Returns:
            List of trip patterns
        """
        # Prepare GraphQL variables for direct routing
        variables = self.__prepare_variables(
            origin,
            destination,
            mode,
            mode_speed
        )

        # Execute query using shared OTPBase executor
        parsed =  await self._execute_query(
            self.QUERY,
            variables,
            OTPPublicQueryResponse.model_validate,
            fallback=None
        )

        # Return empty list if parsing failed
        if not parsed:
            return []
        
        return parsed.trip.tripPatterns
    
    def __prepare_variables(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: Literal["foot", "bicycle"],
        mode_speed: float
    ) -> Dict[str, Any]:
        """
        
        """
        return {
            "from": {
                "coordinates": {
                    "latitude": origin[0],
                    "longitude": origin[1]
                }
            },
            "to": {
                "coordinates": {
                    "latitude": destination[0],
                    "longitude": destination[1]
                }
            },
            "modes": {
                "directMode": mode,
            },
            "walkSpeed": mode_speed / 3.6,
            "bikeSpeed": mode_speed / 3.6,
            "arriveBy": self._ctx.data.arrive_by
        }

# End of file foot_bicycle_base.py
