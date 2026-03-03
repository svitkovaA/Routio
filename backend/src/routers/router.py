"""
file: router.py

Defines the abstract base interface for all transport mode routers.
"""

from abc import ABC, abstractmethod
from typing import List
from models.planning_context import PlanningContext
from models.route import TripPattern

class Router(ABC):
    """
    Abstract base class.
    """
    @abstractmethod
    async def route_group(self, context: PlanningContext) -> List[TripPattern]:
        """
        Computes routing results for a given waypoint group.
        """
        pass

# End of file router.py
