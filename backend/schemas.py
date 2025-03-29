from pydantic import BaseModel


class TransportTable(BaseModel):
    suppliers: list[float | int]
    consumers: list[float | int]
    price_matrix: list[list[float | int]]
    restrictions: dict[str, str] = None
    capacities: list[list[float | int]] = None


class Solution(BaseModel):
    price: float | int
    is_optimal: bool
    roots: list[dict[str, int | float]]
