import random
import numpy as np
from numpy import typing as npt


MAIN_ANSWER = 42


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
                    supplier_epsilon: int) -> bool:
    main_expression = consumer_amount != 0 and supplier_amount != 0
    epsilon_expression = supplier_epsilon != 0 and consumer_epsilon != 0
    mixed_consumer_expression = consumer_amount != 0 and supplier_epsilon != 0
    mixed_supplier_expression = supplier_amount != 0 and consumer_epsilon != 0
    if main_expression or mixed_consumer_expression or mixed_supplier_expression or epsilon_expression:
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
            random.randint(0, 10) for _ in range(consumers_amount)
        ]
        for _ in range(suppliers_amount)
    ]
    return suppliers, consumers, price_matrix


def find_line_penalty(line: npt.NDArray) -> int | float:
    filtered_array = np.fromiter((root for root in line
                                  if root_validation(root.consumer.goods_amount, root.supplier.goods_amount,
                                                     root.consumer.epsilon, root.supplier.epsilon)), dtype=line.dtype)
    if len(filtered_array) == 0:
        return 0
    filtered_array.sort()
    if len(filtered_array) > 1:
        return abs(filtered_array[0].price - filtered_array[1].price)
    return filtered_array[0].price


def get_min_line_element(line: npt.NDArray) -> tuple[int | None, int | None]:
    copied_matrix = line.copy()
    copied_matrix.sort()
    for root in copied_matrix:
        if root_validation(root.consumer.goods_amount, root.supplier.goods_amount, root.consumer.epsilon,
                           root.supplier.epsilon):
            return root.supplier.id, root.consumer.id
    return None, None


def get_all_indices(filed_indices):
    yield from filed_indices
