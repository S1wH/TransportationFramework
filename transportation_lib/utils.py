import random
import numpy as np
from numpy import typing as npt


MAIN_ANSWER = 42
EPSILON_VAL = 1e-6
M_VAL = 1e+12


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px = self.find(x)
        py = self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1


def create_eps_expression(eps: int, goods_amount: int | float) -> str:
    if eps == 0:
        return str(goods_amount)
    epsilon = '\u03B5'
    sign = '+'
    if eps < 0:
        sign = '-'
    if goods_amount == 0:
        return f'{sign if sign == "-" else ""}{eps}{epsilon}'
    return str(goods_amount) if eps == 0 else f'{goods_amount}{sign}{abs(eps) if abs(eps) != 1 else ""}{epsilon}'


def root_validation(consumer_amount: int | float, supplier_amount: int | float, consumer_epsilon: int,
                    supplier_epsilon: int, is_capacity_full: bool) -> bool:
    main_expression = consumer_amount != 0 and supplier_amount != 0
    epsilon_expression = supplier_epsilon != 0 and consumer_epsilon != 0
    mixed_consumer_expression = consumer_amount != 0 and supplier_epsilon != 0
    mixed_supplier_expression = supplier_amount != 0 and consumer_epsilon != 0
    if ((main_expression or mixed_consumer_expression or mixed_supplier_expression or epsilon_expression) and
            not is_capacity_full):
        return True
    return False


def generate_table(suppliers_amount: int, consumers_amount: int, balanced: bool=True):
    random.seed(MAIN_ANSWER)
    suppliers = [random.randint(1, 100) for _ in range(suppliers_amount)]
    consumers = [random.randint(1, 100) for _ in range(consumers_amount)]
    suppliers_sum = sum(suppliers)
    consumers_sum = sum(consumers)
    if balanced is True and suppliers_sum != consumers_sum:
        if suppliers_sum > consumers_sum:
            consumers[-1] += abs(suppliers_sum - consumers_sum)
        else:
            suppliers[-1] += abs(suppliers_sum - consumers_sum)
    price_matrix = [
        [
            random.randint(1, 10) for _ in range(consumers_amount)
        ]
        for _ in range(suppliers_amount)
    ]
    return suppliers, consumers, price_matrix


def find_line_penalty(line: npt.NDArray, basic_plan: npt.NDArray[npt.NDArray]) -> int | float:
    filtered_array = np.fromiter((root for root in line
                                  if root_validation(root.consumer.goods_amount, root.supplier.goods_amount,
                                                     root.consumer.epsilon, root.supplier.epsilon,
                                                     basic_plan[root.supplier.id][root.consumer.id].amount
                                                     == root.capacity)), dtype=line.dtype)
    if len(filtered_array) == 0:
        return 0
    filtered_array.sort()
    if len(filtered_array) > 1:
        return abs(filtered_array[0].price - filtered_array[1].price)
    return filtered_array[0].price


def get_min_line_element(line: npt.NDArray, basic_plan: npt.NDArray[npt.NDArray]) -> tuple[int | None, int | None]:
    copied_matrix = line.copy()
    copied_matrix.sort()
    for root in copied_matrix:
        is_capacity_full = basic_plan[root.supplier.id][root.consumer.id].amount == root.capacity
        if root_validation(root.consumer.goods_amount, root.supplier.goods_amount, root.consumer.epsilon,
                           root.supplier.epsilon, is_capacity_full):
            return root.supplier.id, root.consumer.id
    return None, None


def get_all_indices(filed_indices):
    yield from filed_indices


def find_acyclic_plan(basic_plan_cells, reserve_cells, m, n, used_plans):
    reserve_cells_copy = reserve_cells.copy()

    # Инициализация Union-Find для m поставщиков и n потребителей
    uf = UnionFind(m + n)

    # Копируем все элементы из basic_plan_cells в результат
    selected = [(root.supplier.id, root.consumer.id) for root in basic_plan_cells]
    unselected = []

    # Учитываем компоненты связности от basic_plan_cells
    for root in basic_plan_cells:
        uf.union(root.supplier.id - 1, m + root.consumer.id  - 1)

    while len(selected) !=  m + n - 1:
        root = random.choice(reserve_cells_copy)
        if uf.find(root.supplier.id - 1) != uf.find(m + root.consumer.id - 1):
            selected.append((root.supplier.id, root.consumer.id))
            uf.union(root.supplier.id - 1, m + root.consumer.id - 1)

    selected.sort()
    if selected in used_plans:
        find_acyclic_plan(basic_plan_cells, reserve_cells, m, n, used_plans)
    used_plans.append(selected)

    for root in reserve_cells_copy:
        if root.amount == 0:
            unselected.append((root.supplier.id, root.consumer.id, 'c'))
        elif root.amount == root.capacity:
            unselected.append((root.supplier.id, root.consumer.id, 'd'))

    return selected, unselected
