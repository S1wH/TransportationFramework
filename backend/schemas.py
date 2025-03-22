from pydantic import BaseModel
from typing import List


class TransportTable(BaseModel):
    suppliers: List[float | int]
    consumers: List[float | int]
    price_matrix: List[List[float | int]]
    restrictions: dict[tuple[int, int], tuple[str, int]] = None
    capacities: list[list[float | int]] = None


class Solution(BaseModel):
    price: float | int
    transition_matrix: List[List[str]]
    is_optimal: bool
