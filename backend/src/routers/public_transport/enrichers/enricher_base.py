from abc import ABC, abstractmethod
from models.route import TripPattern

class EnricherBase(ABC):
    @abstractmethod
    async def enrich(self, trip_pattern: TripPattern) -> None:
        pass
