"""
file: selector_base.py

Base abstraction for bicycle station/rack selection strategies
"""

from abc import ABC
from typing import List, Tuple, TypeVar
import numpy as np
from scipy.spatial.distance import cosine
from models.route import BikeStationNodeBase

# Generic type representing a concrete BikeStationNodeBase subtype
T = TypeVar("T", bound=BikeStationNodeBase)

class SelectorBase(ABC):
    """
    Abstract base class for station/rack selection logic.
    """
    def __init__(self, max_distance: float = 1000):
        """
        Initializes the selector.

        Args:
            max_distance: Maximum allowed distance in meters for candidate
            station/rack consideration
        """
        self._max_distance = max_distance

    @staticmethod
    def _sort_and_limit(
        scored_nodes: List[T],
        discarded_nodes: List[T],
        limit: int = 10
    ) -> List[T]:
        """
        Sorts stations/racks by score in descending order and limits the result size.

        Args:
            scored_nodes: Stations/racks that passed filtering and were scored
            discarded_nodes: Stations/racks filtered out but usable as fallback
            limit: Maximum number of stations to return

        Returns:
            Top N stations sorted by descending score
        """
        # Fallback to discarded nodes if no valid scored nodes remain
        if not scored_nodes:
            scored_nodes = discarded_nodes

        # Sorted and limited stations/racks by descending score
        return sorted(scored_nodes, key=lambda x: x.score, reverse=True)[:limit]

    @staticmethod
    def _compute_normalized_angle(vector1: np.ndarray, vector2: np.ndarray) -> float:
        """
        Computes normalized cosine similarity between two vectors. The result
        is scaled from range (-1,1) to (0,1).

        Args:
            vector1: First direction vector
            vector2: Second direction vector

        Returns:
            Normalized similarity value
        """
        # Compute cosine similarity
        similarity = 1 - cosine(vector1, vector2)

        # Normalize computed similarity
        return (similarity + 1) * 0.5
    
    @staticmethod
    def _direction_vector(
        source: Tuple[float, float],
        target: Tuple[float, float]
    ) -> np.ndarray:
        """
        Computes a direction vector from source to target coordinates.

        Args:
            source: Latitude, longitude of the source point
            target: Latitude, longitude of the target point

        Returns:
            Numpy array representing the direction vector
        """
        return np.asarray(target, dtype=np.float64) - np.asarray(source, dtype=np.float64)
    
    @staticmethod
    def _is_in_forward_direction(
        base_vector: np.ndarray,
        candidate_vector: np.ndarray
    ) -> bool:
        """
        Determines whether a candidate vector points are in the forward
        direction relative to a base vector.

        Args:
            base_vector: Reference direction vector
            candidate_vector: Candidate direction vector

        Returns:
            True if candidate is in forward direction, false otherwise.
        """
        return np.dot(base_vector, candidate_vector) > 0

# End of file selector_base.py
