"""
file: bicycle_router_base.py

Abstract base class for bicycle routers.
"""

from abc import ABC, abstractmethod
import asyncio
import numpy as np
from typing import List, Tuple, final
from routing_engine.routing_context import RoutingContext
from routers.router_base import RouterBase
from otp.bicycle import OTPBicycle
from otp.foot import OTPFoot
from models.planning_context import PlanningContext
from models.route import TripPattern

class BicycleRouterBase(RouterBase, ABC):
    """
    Abstract base class for bicycle routing implementations.   
    """
    def __init__(self, context: RoutingContext) -> None:
        """
        Initializes bicycle routing infrastructure.

        Args:
            context: Global routing context containing configuration
        """
        # Initialize base router context
        super().__init__(context)

        # OTP client for bicycle routing
        self._otp_bicycle_client = OTPBicycle(self._ctx)

        # OTP client for walking
        self._otp_foot_client = OTPFoot(self._ctx)
        
    @abstractmethod
    async def route_bike_group(self, context: PlanningContext) -> List[TripPattern]:
        """
        Routes a bicycle trip for a group. Must be implemented by concrete
        routers.

        Args:
            context: Planning context with routing parameters

        Returns:
            List of computed trip patterns
        """
        pass

    @final
    async def _route_bicycle_segments(self, waypoints: List[str]) -> List[TripPattern]:
        """
        Routes consecutive bicycle segments between waypoints.

        Args:
            waypoints: Ordered list of waypoint coordinates

        Returns:
            List of merged trip patterns
        """
        # Create OTP routing tasks for each consecutive segment
        tasks = [
            self._otp_bicycle_client.execute(
                self._parse_coordinates(waypoints[i]),
                self._parse_coordinates(waypoints[i + 1])
            )
            for i in range(len(waypoints) - 1)
        ]

        results = await asyncio.gather(*tasks)

        trip_patterns: List[TripPattern] = []

        # Merge segment results into a single pattern chain
        for result in results:
            # Initialize with first segment result
            if not trip_patterns:
                trip_patterns = result
            # Append next segment legs to existing patterns
            else:
                for pattern in trip_patterns:
                    pattern.legs.extend(result[0].legs)

        return trip_patterns

    @final
    @staticmethod
    def _compute_bisector(
        A: Tuple[float, float],
        B: Tuple[float, float],
        C: Tuple[float, float]
    ) -> np.ndarray:
        """
        Computes the normalized angle bisector vector at point B.

        Args:
            A: Coordinate of the first point
            B: Vertex point where the bisector is computed
            C: Coordinate of the second point

        Returns:
            Normalized bisector direction vector originating from B
        """
        # Compute vectors BA and BC
        BA = np.asarray(A) - np.asarray(B)
        BC = np.asarray(C) - np.asarray(B)

        # Normalize both vectors
        BA_norm = BA / np.linalg.norm(BA)
        BC_norm = BC / np.linalg.norm(BC)

        # Sum normalized vectors to obtain angle bisector
        bisector = BA_norm + BC_norm

        # Handle case where vectors are opposite
        if np.linalg.norm(bisector) < 1e-6:
            return BC_norm
        
        # Return normalized bisector vector
        return bisector / np.linalg.norm(bisector)

# End of file bicycle_router_base.py
