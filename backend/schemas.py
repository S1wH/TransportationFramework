from typing import Optional
from pydantic import BaseModel


class TransportTable(BaseModel):
    id: Optional[int]
    name: Optional[str]
    suppliers: list[float | int]
    consumers: list[float | int]
    price_matrix: list[list[float | int]]
    restrictions: Optional[dict[str, str]] = None
    capacities: Optional[list[list[float | int]]] = None
    user_id: Optional[int]


class Solution(BaseModel):
    price: float | int
    is_optimal: bool
    roots: list[dict[str, int | float]]


class User(BaseModel):
    username: str
    password: str
