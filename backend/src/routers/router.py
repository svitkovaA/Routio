from abc import ABC, abstractmethod
from typing import List
from models.planning_context import PlanningContext
from models.route import TripPattern

class Router(ABC):
    @abstractmethod
    async def route_group(self, context: PlanningContext) -> List[TripPattern]:
        pass
