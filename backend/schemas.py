from pydantic import BaseModel, validator
from typing import List


class TransportTable(BaseModel):
    suppliers: List[float | int]
    consumers: List[float | int]
    price_matrix: List[List[float | int]]
    restrictions: dict[tuple[int, int], tuple[str, int]] = {}
    capacities: list[list[float | int]] = None
