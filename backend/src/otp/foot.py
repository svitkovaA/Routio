"""
file: foot.py

OpenTripPlanner client for walking routes.
"""

from typing import List, Tuple
from models.route import TripPattern
from otp.foot_bicycle_base import OTPFootBicycleBase

class OTPFoot(OTPFootBicycleBase):
    """
    OTP client for walking route computation.
    """
    async def execute(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float]
    ) -> List[TripPattern]:
        """
        Executes walking route query.

        Args:
            origin: Coordinates in format lat, lon of starting point
            destination: Coordinates in format lat, lon of destination point

        Returns:
            List of trip patterns
        """
        return await self._base_execute(
            origin,
            destination,
            "foot",
            self._ctx.data.walk_speed
        )

# End of file foot.py
