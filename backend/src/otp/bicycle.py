from typing import List, Tuple
from models.route import TripPattern
from otp.foot_bicycle_base import OTPFootBicycleBase

class OTPBicycle(OTPFootBicycleBase):
    async def execute(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float]
    ) -> List[TripPattern]:
        return await self._base_execute(
            origin,
            destination,
            "bicycle",
            self._ctx.bike_speed
        )