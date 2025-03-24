from pydantic import BaseModel
from typing import List, Dict, Tuple


class TransportTable(BaseModel):
    suppliers: List[float | int]
    consumers: List[float | int]
    price_matrix: List[List[float | int]]
    restrictions: dict[tuple[int, int], tuple[str, int]] = None
    capacities: list[list[float | int]] = None


class Solution(BaseModel):
    price: float | int
    is_optimal: bool
    transition_matrix: List[List[str]]


class InputSolution(BaseModel):
    price: float | int
    is_optimal: bool
    roots: Dict[Tuple[int, int], Tuple[float | int, int]]
