"""
file: enricher_base.py

Defines the abstract base class for trip pattern enrichers.
"""

from abc import ABC, abstractmethod
from models.route import TripPattern

class EnricherBase(ABC):
    """
    Abstract base class for all trip pattern enrichers.
    """
    @abstractmethod
    async def enrich(self, trip_pattern: TripPattern) -> None:
        """
        Enriches a trip pattern with additional information.

        Args:
            trip_pattern: TripPattern instance to be enriched
        """
        pass

# End of file enricher_base.py
