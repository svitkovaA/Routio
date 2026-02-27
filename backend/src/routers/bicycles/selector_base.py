from abc import ABC
from typing import List, Tuple, TypeVar
import numpy as np
from scipy.spatial.distance import cosine
from models.route import BikeStationNodeBase

T = TypeVar("T", bound=BikeStationNodeBase)

class SelectorBase(ABC):
    def __init__(self, max_distance: float = 1000):
        self._max_distance = max_distance

    @staticmethod
    def _sort_and_limit(
        scored_nodes: List[T],
        discarded_nodes: List[T],
        limit: int = 10
    ) -> List[T]:
        # If all stations were filtered out by constraint use previously discarded stations
        if not scored_nodes:
            scored_nodes = discarded_nodes

        # Sort stations by descending score
        return sorted(scored_nodes, key=lambda x: x.score, reverse=True)[:limit]

    @staticmethod
    def _compute_normalized_angle(vector1: np.ndarray, vector2: np.ndarray) -> float:
        similarity = 1 - cosine(vector1, vector2)
        return (similarity + 1) * 0.5
    
    @staticmethod
    def _direction_vector(
        source: Tuple[float, float],
        target: Tuple[float, float]
    ) -> np.ndarray:
        return np.asarray(target, dtype=np.float64) - np.asarray(source, dtype=np.float64)
    
    @staticmethod
    def _is_in_forward_direction(
        base_vector: np.ndarray,
        candidate_vector: np.ndarray
    ) -> bool:
        return np.dot(base_vector, candidate_vector) > 0
