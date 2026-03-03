"""
file: bicycle.py

OpenTripPlanner client for direct bicycle routing.
"""

from typing import List, Tuple
from models.route import TripPattern
from otp.foot_bicycle_base import OTPFootBicycleBase

class OTPBicycle(OTPFootBicycleBase):
    """
    OTP client for direct bicycle route computation.
    """
    async def execute(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float]
    ) -> List[TripPattern]:
        """
        Executes bicycle route query.

        Args:
            origin: Coordinates inf format lat, lon of starting point
            destination: Coordinates in format lat, lon of destination point

        Returns:
            List of trip patterns
        """
        return await self._base_execute(
            origin,
            destination,
            "bicycle",
            self._ctx.bike_speed
        )
    
# End of file bicycle.py
