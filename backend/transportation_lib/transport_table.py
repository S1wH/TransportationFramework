import copy
from collections import deque
from typing import Optional, List, Dict
from abc import ABC
from prettytable import PrettyTable
from .transport_errors import (InvalidMatrixDimension, InvalidPriceValueError, InvalidAmountGood,
                               InvalidRestrictionValue, InvalidRestrictionIndices, InvalidRestrictionSymbol,
                               InvalidCapacityValue, InvalidCapacitiesDimension)
from .utils import *


class Participant(ABC):
    def __init__(self, goods_amount: int | float, obj_id: int, epsilon: int=0) -> None:
        self.goods_amount = goods_amount
        self.real_amount = goods_amount
        self.epsilon = epsilon
        self.real_epsilon = epsilon
        self.id = obj_id

    def __lt__(self, other) -> bool:
        if isinstance(other, Participant):
            return self.goods_amount < other.goods_amount
        return self.goods_amount < other

    def __le__(self, other) -> bool:
        if isinstance(other, Participant):
            return self.goods_amount <= other.goods_amount
        return self.goods_amount <= other

    def __gt__(self, other) -> bool:
        if isinstance(other, Participant):
            return self.goods_amount > other.goods_amount
        return self.goods_amount > other

    def __ge__(self, other) -> bool:
        if isinstance(other, Participant):
            return self.goods_amount >= other.goods_amount
        return self.goods_amount >= other

    def __eq__(self, other) -> bool:
        if isinstance(other, Participant):
            return self.goods_amount == other.goods_amount
        return self.goods_amount == other

    def __ne__(self, other):
        if isinstance(other, Participant):
            return self.goods_amount != other.goods_amount
        return self.goods_amount != other


class Consumer(Participant):
    pass


class Supplier(Participant):
    pass


class Root:
    def __init__(self, price: int | float, supplier: Supplier, consumer: Consumer, amount=0, epsilon=0,
                 representation='0', capacity=None) -> None:
        self.capacity = capacity
        self.price = price
        self.epsilon = epsilon
        self.amount = amount
        self.supplier = supplier
        self.consumer = consumer
        self.repr = representation

    def __lt__(self, other):
        return self.price < other.price

    def __le__(self, other):
        return self.price <= other.price

    def __gt__(self, other):
        return self.price > other.price

    def __ge__(self, other):
        return self.price >= other.price

    def __eq__(self, other):
        if not hasattr(other, 'price'):
            return self.repr == other
        return self.price == other.price

    def __copy__(self):
        return Root(self.price, self.supplier, self.consumer, self.amount, self.epsilon, self.repr, self.capacity)


class TransportTable:
    def __init__(self, suppliers: list[float | int], consumers: list[float | int],
                 price_matrix: npt.NDArray[npt.NDArray[float]], restrictions: dict[tuple[int, int],
            tuple[str, int]]=None, capacities: list[list[float | int]]=None) -> None:
        self.__suppliers_amount = len(suppliers)
        self.__consumers_amount = len(consumers)
        self.__suppliers = np.array([Supplier(supplier, supplier_id)
                                     for supplier_id, supplier in enumerate(suppliers)], dtype=Supplier)
        self.__consumers = np.array([Consumer(consumer, consumer_id)
                                     for consumer_id, consumer in enumerate(consumers)], dtype=Consumer)
        self.__restrictions = restrictions
        self.__price_matrix = np.zeros((self.__suppliers_amount, self.__consumers_amount), dtype=Root)
        self.__capacities = capacities

        for supplier_id, prices in enumerate(price_matrix):
            for consumer_id, price in enumerate(prices):
                supplier = self.__suppliers[supplier_id]
                consumer = self.__consumers[consumer_id]
                self.__price_matrix[supplier_id][consumer_id] = Root(price, supplier, consumer)

        self.__validate_table()

        if self.__capacities is not None:
            self.__capacities = np.array(self.__capacities)
            self.__validate_capacities()
            for supplier_id, prices in enumerate(price_matrix):
                for consumer_id, price in enumerate(prices):
                    self.__price_matrix[supplier_id][consumer_id].capacity = self.__capacities[supplier_id][consumer_id]

        self.__basic_plan = np.zeros((self.__suppliers_amount, self.__consumers_amount), dtype=Root)
        self.__solution = np.zeros((self.__suppliers_amount, self.__consumers_amount))

    def pprint(self) -> None:
        table = PrettyTable([''] + [f'T{i + 1}' for i in range(self.price_matrix[0].size)] + ['A'])
        for i in range(self.price_matrix.shape[0]):
            row = [f'S{i + 1}']
            for j in range(self.price_matrix[i].size):
                row.append(self.price_matrix[i][j].price if self.price_matrix[i][j].price != M_VAL else 'M')
            row.append(create_eps_expression(self.suppliers[i].real_epsilon, self.suppliers[i].real_amount))
            table.add_row(row)
        row = ['B']
        for i in range(self.consumers.size):
            row.append(create_eps_expression(self.consumers[i].real_epsilon, self.consumers[i].real_amount))
        row.append('')
        table.add_row(row)
        print(table)

    def pprint_res(self, solution: npt.NDArray[npt.NDArray[np.float16]]) -> None:
        table = PrettyTable([''] + [f'T{i + 1}' for i in range(self.price_matrix[0].size)] + ['A'])
        for i in range(len(solution)):
            row = [f'S{i + 1}']
            for j in range(len(solution[i])):
                row.append(solution[i][j].repr)
            row.append(create_eps_expression(self.suppliers[i].real_epsilon, self.suppliers[i].real_amount))
            table.add_row(row)
        row = ['B']
        for i in range(self.consumers.size):
            row.append(create_eps_expression(self.consumers[i].real_epsilon, self.consumers[i].real_amount))
        row.append('')
        table.add_row(row)
        print(table)

    def check_table_balance(self) -> bool:
        goods = np.vectorize(lambda x: x.goods_amount)
        return np.sum(goods(self.suppliers)) == np.sum(goods(self.consumers))

    def __restore_price_matrix_values(self) -> None:
        for supplier in self.suppliers:
            supplier.goods_amount = supplier.real_amount
        for consumer in self.consumers:
            consumer.goods_amount = consumer.real_amount

    def __get_min_valid_root(self) -> Optional[Root]:
        reshaped_matrix = self.price_matrix.copy().reshape(-1)
        reshaped_matrix.sort()
        for root in reshaped_matrix:
            if root_validation(root.consumer.goods_amount, root.supplier.goods_amount, root.consumer.epsilon,
                               root.supplier.epsilon,
                               self.__basic_plan[root.supplier.id][root.consumer.id].amount == root.capacity):
                return root
        return None

    def __get_min_cell_value(self, root: Root) -> tuple[int | float, int]:
        if self.__capacities is not None:
            available_capacity = root.capacity - self.__basic_plan[root.supplier.id][root.consumer.id].amount
            min_goods = min(root.supplier.goods_amount, root.consumer.goods_amount, available_capacity)
            if min_goods == root.supplier.goods_amount:
                eps = root.supplier.epsilon
            elif min_goods == root.consumer.goods_amount:
                eps = root.consumer.epsilon
            else:
                eps = 0
            return min_goods, eps
        else:
            if root.consumer.goods_amount < root.supplier.goods_amount:
                return root.consumer.goods_amount, root.consumer.epsilon
            elif root.consumer.goods_amount > root.supplier.goods_amount:
                return root.supplier.goods_amount, root.supplier.epsilon
            else:
                return root.supplier.goods_amount, min(root.supplier.epsilon, root.consumer.epsilon)

    def __validate_capacities(self) -> None:
        if (self.__capacities.shape[0] != self.__suppliers_amount or
                self.__capacities.shape[1] != self.__consumers_amount):
            raise InvalidCapacitiesDimension(self.__capacities.shape, self.price_matrix.shape)

        row_sums = self.__capacities.sum(axis=1)
        column_sums = self.__capacities.sum(axis=0)
        for idx, row_sum in enumerate(row_sums):
            if row_sum < self.suppliers[idx]:
                raise InvalidCapacityValue(row_sum, self.suppliers[idx].goods_amount, idx + 1, 0)
        for idx, column_sum in enumerate(column_sums):
            if column_sum < self.consumers[idx]:
                raise InvalidCapacityValue(column_sum, self.suppliers[idx].goods_amount, idx + 1, 0)

    def __validate_table(self) -> None:
        for supplier_id, supplier in enumerate(self.suppliers):
            if not isinstance(supplier.goods_amount, (int, float)) or supplier <= 0:
                raise InvalidAmountGood(supplier, 0, supplier_id)

        for consumer_id, consumer in enumerate(self.consumers):
            if not isinstance(consumer.goods_amount, (int, float)) or consumer <= 0:
                raise InvalidAmountGood(consumer, 1, consumer_id)

        for supplier_id, prices in enumerate(self.price_matrix, 1):
            if len(prices) != self.__consumers_amount:
                raise InvalidMatrixDimension(self.__consumers_amount, len(prices))
            for consumer_id, root in enumerate(prices, 1):
                if not isinstance(root.price, (int, float, np.float16)) or root.price < 0:
                    raise InvalidPriceValueError(root.price, (supplier_id, consumer_id))

        if self.__restrictions:
            for cell, restriction in self.__restrictions.items():
                if not self.__suppliers_amount > cell[0] >= 0 or not self.__consumers_amount > cell[1] >= 0:
                    raise InvalidRestrictionIndices(cell,
                                                    (self.__suppliers_amount, self.__consumers_amount))
                if restriction[0] not in ['>', '<']:
                    raise InvalidRestrictionSymbol(restriction[0])

                consumer_value = self.price_matrix[cell[0]][cell[1]].consumer
                supplier_value = self.price_matrix[cell[0]][cell[1]].supplier
                if restriction[1] > consumer_value or restriction[1] > supplier_value or restriction[1] < 0:
                    raise InvalidRestrictionValue(restriction[1], (0,
                                                                   min(consumer_value, supplier_value).real_amount))

    def __make_table_balanced(self) -> None:
        goods = np.vectorize(lambda x: x.goods_amount)
        total_suppliers_goods = np.sum(goods(self.suppliers))
        total_consumers_goods = np.sum(goods(self.consumers))
        abs_difference = abs(total_suppliers_goods - total_consumers_goods)
        if total_suppliers_goods > total_consumers_goods:
            self.__consumers_amount += 1
            new_consumer = Consumer(abs_difference, self.__consumers_amount - 1)
            self.__consumers = np.append(self.__consumers, new_consumer)
            new_line = np.empty((self.__suppliers_amount, 1), dtype=Root)
            for i in range(self.__suppliers_amount):
                new_line[i][0] = Root(0, self.suppliers[i], new_consumer)
            self.__price_matrix = np.concatenate((self.__price_matrix, new_line), axis=1)
        else:
            self.__suppliers_amount += 1
            new_supplier = Supplier(abs_difference,  self.__suppliers_amount - 1)
            self.__suppliers = np.append(self.__suppliers, new_supplier)
            new_line = np.empty((1, self.__consumers_amount), dtype=Root)
            for i in range(self.__consumers_amount):
                new_line[0][i] = Root(0, new_supplier, self.consumers[i])
            self.__price_matrix = np.concatenate((self.price_matrix, new_line), axis=0)

    def __epsilon_modify_table(self) -> None:
        for supplier in self.suppliers:
            supplier.epsilon = 1
            supplier.real_epsilon = 1
        self.consumers[-1].epsilon = self.__suppliers_amount
        self.consumers[-1].real_epsilon = self.__suppliers_amount

    def __check_balance_equations(self) -> bool:
        for supplier in self.suppliers:
            if supplier.goods_amount != 0 or supplier.epsilon != 0:
                return False
        for consumer in self.consumers:
            if consumer.goods_amount != 0 or consumer.epsilon != 0:
                return False
        return True

    def __get_disbalanced_participants(self) -> tuple[dict[int, tuple[int, float]], dict[int, tuple[int, float]]]:
        disbalanced_suppliers = {}
        disbalanced_consumers = {}
        for supplier in self.suppliers:
            if supplier.goods_amount != 0 or supplier.epsilon != 0:
                disbalanced_suppliers[supplier.id] = (supplier.goods_amount, supplier.epsilon)
        for consumer in self.consumers:
            if consumer.goods_amount != 0 or consumer.epsilon != 0:
                disbalanced_consumers[consumer.id] = (consumer.goods_amount, consumer.epsilon)
        return disbalanced_suppliers, disbalanced_consumers

    def __north_western_method(self) -> tuple[npt.NDArray[Root], int | float]:
        self.__basic_plan = np.zeros((self.__suppliers_amount, self.__consumers_amount), dtype=Root)
        for supplier_id in range(self.__suppliers_amount):
            for consumer_id in range(self.__consumers_amount):
                self.__basic_plan[supplier_id][consumer_id] = copy.copy(self.price_matrix[supplier_id][consumer_id])

        consumer_id = 0
        supplier_id = 0
        cost = 0
        while consumer_id != self.__consumers_amount and supplier_id != self.__suppliers_amount:
            root = self.price_matrix[supplier_id][consumer_id]
            goods_amount, eps = self.__get_min_cell_value(root)
            self.__basic_plan[supplier_id][consumer_id].amount = goods_amount
            self.__basic_plan[supplier_id][consumer_id].epsilon = eps
            self.__basic_plan[supplier_id][consumer_id].repr = create_eps_expression(eps, goods_amount)
            cost += root.price * goods_amount
            if (root.consumer < root.supplier or
                    (root.consumer.epsilon < root.supplier.epsilon and root.consumer == root.supplier)):
                root.supplier.goods_amount -= goods_amount
                root.supplier.epsilon -= eps
                consumer_id += 1
            elif (root.consumer > root.supplier or
                  (root.consumer.epsilon > root.supplier.epsilon and root.consumer == root.supplier)):
                root.consumer.goods_amount -= goods_amount
                root.consumer.epsilon -= eps
                supplier_id += 1
            else:
                if supplier_id == self.__suppliers_amount - 1 and consumer_id == self.__consumers_amount - 1:
                    break
                self.__restore_price_matrix_values()
                self.__epsilon_modify_table()
                return self.__north_western_method()
        return self.__basic_plan, cost

    def __minimum_cost_method(self) -> tuple[npt.NDArray[Root], int | float]:
        self.__basic_plan = np.zeros((self.__suppliers_amount, self.__consumers_amount), dtype=Root)
        for supplier_id in range(self.__suppliers_amount):
            for consumer_id in range(self.__consumers_amount):
                self.__basic_plan[supplier_id][consumer_id] = copy.copy(self.price_matrix[supplier_id][consumer_id])

        counter = 0
        cost = 0
        root = self.__get_min_valid_root()
        while root:
            goods_amount, eps = self.__get_min_cell_value(root)
            cost += root.price * goods_amount

            root.supplier.goods_amount -= goods_amount
            root.consumer.goods_amount -= goods_amount
            if root.consumer == root.supplier:
                eps = min(root.consumer.epsilon, root.supplier.epsilon)
            root.supplier.epsilon -= eps
            root.consumer.epsilon -= eps

            self.__basic_plan[root.supplier.id][root.consumer.id].amount = goods_amount
            self.__basic_plan[root.supplier.id][root.consumer.id].epsilon = eps
            self.__basic_plan[root.supplier.id][root.consumer.id].repr = create_eps_expression(eps, goods_amount)
            counter += 1

            root = self.__get_min_valid_root()

        if counter < self.__consumers_amount + self.__suppliers_amount - 1:
            self.__restore_price_matrix_values()
            self.__epsilon_modify_table()
            return self.__minimum_cost_method()

        return self.__basic_plan, cost

    def __vogel_method(self) -> tuple[npt.NDArray[Root], int | float]:
        self.__basic_plan = np.zeros((self.__suppliers_amount, self.__consumers_amount), dtype=Root)
        for supplier_id in range(self.__suppliers_amount):
            for consumer_id in range(self.__consumers_amount):
                self.__basic_plan[supplier_id][consumer_id] = copy.copy(self.price_matrix[supplier_id][consumer_id])

        cost = 0
        counter = 0

        while True:
            line_type, line_index = self.__get_max_penalty_line()
            if line_index is None:
                break
            line = self.__basic_plan[line_index] if line_type == 'row' else self.__basic_plan[:, line_index]
            root = self.__get_min_cost_cell(line)
            if not root:
                break

            supplier_idx = root.supplier.id
            consumer_idx = root.consumer.id

            if hasattr(root, 'capacity') and root.capacity:
                amount = min(root.supplier.goods_amount, root.consumer.goods_amount, root.capacity)
            else:
                amount = min(root.supplier.goods_amount, root.consumer.goods_amount)

            if root.consumer.goods_amount == root.supplier.goods_amount:
                eps = min(root.consumer.epsilon, root.supplier.epsilon)
            elif root.consumer.goods_amount == 0 and root.consumer.epsilon > root.supplier.epsilon:
                eps = min(root.consumer.epsilon, root.supplier.epsilon)
            elif root.supplier.goods_amount == 0 and root.supplier.epsilon < root.consumer.epsilon:
                eps = min(root.consumer.epsilon, root.supplier.epsilon)
            else:
                eps = max(root.consumer.epsilon, root.supplier.epsilon)

            self.__basic_plan[supplier_idx][consumer_idx].amount = amount

            root.supplier.goods_amount -= amount
            root.consumer.goods_amount -= amount
            root.supplier.epsilon -= eps
            root.consumer.epsilon -= eps

            self.__basic_plan[root.supplier.id][root.consumer.id].amount = amount
            self.__basic_plan[root.supplier.id][root.consumer.id].epsilon = eps
            self.__basic_plan[root.supplier.id][root.consumer.id].repr = create_eps_expression(eps, amount)

            cost += root.price * amount
            counter += 1

        if counter < self.__consumers_amount + self.__suppliers_amount - 1:
            self.__restore_price_matrix_values()
            self.__epsilon_modify_table()
            return self.__vogel_method()

        return self.__basic_plan, cost

    def __is_cell_available(self, cell: Root) -> bool:
        supplier_amount = cell.supplier.goods_amount
        consumer_amount = cell.consumer.goods_amount
        supplier_eps = cell.supplier.epsilon
        consumer_eps = cell.consumer.epsilon
        if supplier_amount <= 0 and consumer_amount <= 0 and (supplier_eps <= 0 or consumer_eps <= 0):
            return False
        if (supplier_amount <= 0 or cell.consumer.goods_amount <= 0) and supplier_eps <= 0 and consumer_eps <= 0:
            return False
        if (supplier_amount <= 0 and supplier_eps <= 0) or (consumer_amount <= 0 and consumer_eps <= 0):
            return False
        if self.__restrictions and (cell.supplier.id, cell.consumer.id) in self.__restrictions:
            restriction = self.__restrictions[(cell.supplier.id, cell.consumer.id)]
            if restriction[0] == '>' and cell.amount <= restriction[1]:
                return False
            elif restriction[0] == '<' and cell.amount >= restriction[1]:
                return False
        return True

    def __calculate_penalty(self, line: npt.NDArray[Root]) -> int:
        available_cells = [cell for cell in line if self.__is_cell_available(cell)]
        if not available_cells:
            return 0
        if len(available_cells) == 1:
            return available_cells[0].price
        sorted_cells = sorted(available_cells, key=lambda x: x.price)
        return sorted_cells[1].price - sorted_cells[0].price

    def __get_max_penalty_line(self) -> tuple[Optional[str], Optional[int]]:
        row_penalties = [
            (i, self.__calculate_penalty(self.__basic_plan[i]))
            for i in range(self.__suppliers_amount) if self.__basic_plan[i][0].supplier.goods_amount > 0 or self.__basic_plan[i][0].supplier.epsilon > 0
        ]
        col_penalties = [
            (j, self.__calculate_penalty(self.__basic_plan[:, j]))
            for j in range(self.__consumers_amount) if self.__basic_plan[0][j].consumer.goods_amount > 0 or self.__basic_plan[0][j].consumer.epsilon > 0
        ]

        max_row = max(row_penalties, key=lambda x: x[1], default=(None, 0))
        max_col = max(col_penalties, key=lambda x: x[1], default=(None, 0))

        if max_row[1] >= max_col[1] and max_row[0] is not None:
            return 'row', max_row[0]
        elif max_col[0] is not None:
            return 'col', max_col[0]
        return None, None

    def __get_min_cost_cell(self, line: npt.NDArray[Root]) -> Optional[Root]:
        available_cells = [cell for cell in line if self.__is_cell_available(cell)]
        if not available_cells:
            return None
        return min(available_cells, key=lambda x: x.price)

    def __fill_conditional_values(self, filled_cells: list[tuple[int, int]]=None
                                  ) -> tuple[npt.NDArray[np.float16], npt.NDArray[np.float16]]:
        if not filled_cells:
            new_field_cells =  list(zip(np.where(self.__solution != '0')[0], np.where(self.__solution != '0')[1]))
        else:
            new_field_cells = filled_cells.copy()

        supplier_values = np.zeros(self.__suppliers_amount)
        supplier_values[0] = 0.0
        filled_suppliers_indices = [0]
        consumer_values = np.zeros(self.__consumers_amount)
        filled_consumers_indices = []
        counter = 1

        while counter != self.__suppliers_amount + self.__consumers_amount:
            generator_indices = get_all_indices(new_field_cells)
            for pair in generator_indices:
                supplier_idx, consumer_idx = pair
                if supplier_idx in filled_suppliers_indices:
                    filled_consumers_indices = np.append(filled_consumers_indices, consumer_idx)
                    consumer_values[consumer_idx] = (supplier_values[supplier_idx]
                                                     + np.float16(self.price_matrix[supplier_idx][consumer_idx].price))
                    new_field_cells.remove(pair)
                    break
                if consumer_idx in filled_consumers_indices:
                    filled_suppliers_indices = np.append(filled_suppliers_indices, supplier_idx)
                    supplier_values[supplier_idx] = (consumer_values[consumer_idx]
                                                     - np.float16(self.price_matrix[supplier_idx][consumer_idx].price))
                    new_field_cells.remove(pair)
                    break
            counter += 1
        return supplier_values, consumer_values

    def __calculate_potentials(self, supplier_values: npt.NDArray[np.float16], consumer_values: npt.NDArray[np.float16],
                               filled_cells: list[tuple[int, int]]=None
                               ) -> dict[tuple[npt.NDArray[np.int64], npt.NDArray[np.int64]], np.float16]:
        if not filled_cells:
            filled_cells = list(zip(np.where(self.__solution == '0')[0], np.where(self.__solution == '0')[1]))
        potentials_dict = {}
        for cell in filled_cells:
            supplier_idx = cell[0]
            consumer_idx = cell[1]
            pseudo_price = consumer_values[consumer_idx] - supplier_values[supplier_idx]
            potential = self.price_matrix[supplier_idx][consumer_idx].price - pseudo_price
            potentials_dict[cell] = potential
        return potentials_dict

    def __find_potential_loop(self, min_potential: tuple[tuple[np.int64], np.float16],
                              filled_cells: list[tuple[int, int]]=None) -> list[tuple[np.int64]] | None:
        if not filled_cells:
            new_filled_cells = (list(zip(np.where(self.__solution != '0')[0], np.where(self.__solution != '0')[1]))
                            + [min_potential[0]])
        else:
            new_filled_cells = filled_cells.copy() + [min_potential[0]]
        queue = deque()
        queue.append((min_potential[0][0], min_potential[0][1], [], 'row'))
        queue.append((min_potential[0][0], min_potential[0][1], [], 'col'))
        visited = set()
        while queue:
            i, j, path, next_dir = queue.popleft()
            if (i, j) == (min_potential[0][0], min_potential[0][1]) and len(path) >= 3:
                return path

            if (i, j, next_dir) in visited:
                continue
            visited.add((i, j, next_dir))

            if next_dir == 'row':
                candidates = [cell for cell in new_filled_cells if cell[0] == i and cell != (i, j)]
                for cell in candidates:
                    new_path = path + [(i, j)]
                    queue.append((cell[0], cell[1], new_path, 'col'))
            elif next_dir == 'col':
                candidates = [cell for cell in new_filled_cells if cell[1] == j and cell != (i, j)]
                for cell in candidates:
                    new_path = path + [(i, j)]
                    queue.append((cell[0], cell[1], new_path, 'row'))
        return []

    def __find_min_loop_value(self, loop: list[tuple[np.int64]]) -> tuple[int | float, int]:
        min_value = (self.__solution[loop[1][0]][loop[1][1]].amount +
                     (self.__solution[loop[1][0]][loop[1][1]].epsilon * EPSILON_VAL))
        min_indices = loop[1]
        for i in range(1, len(loop), 2):
            root = self.__solution[loop[i][0]][loop[i][1]]
            cell_amount = root.amount + (root.epsilon * EPSILON_VAL)
            if cell_amount < min_value:
                min_value = cell_amount
                min_indices = loop[i]

        return (self.__solution[min_indices[0]][min_indices[1]].amount,
                self.__solution[min_indices[0]][min_indices[1]].epsilon)

    def __find_min_loop_capacity_value(self, loop: list[tuple[np.int64]]) -> int | float:
        min_value = self.__solution[loop[0][0]][loop[0][1]].capacity
        for i in range(len(loop)):
            root = self.__solution[loop[i][0]][loop[i][1]]
            if i % 2 == 0:
                redistr_val = root.capacity - (root.amount + (root.epsilon * EPSILON_VAL))
            else:
                redistr_val = root.amount + (root.epsilon * EPSILON_VAL)

            min_value = min(min_value, redistr_val)
        return min_value

    def __transportation_redistribution(self, loop: list[tuple[np.int64]], amount: int | float, epsilon: int) -> None:
        for idx, cell in enumerate(loop):
            root = self.__solution[cell[0]][cell[1]]
            if idx % 2 == 0:
                root.amount += amount
                root.epsilon += epsilon
            else:
                root.amount -= amount
                root.epsilon -= epsilon
            root.repr = create_eps_expression(root.epsilon, root.amount)

    def __put_additional_restriction(self, supplier_id: int, consumer_id: int, action: str, amount: int | float):
        root = self.price_matrix[supplier_id][consumer_id]
        if action == '>':
            root.supplier.real_amount -= amount
            root.supplier.goods_amount -= amount
            root.consumer.real_amount -= amount
            root.consumer.goods_amount -= amount
        else:
            prev_amount = self.__suppliers[supplier_id].real_amount
            self.__suppliers[supplier_id].real_amount = amount
            self.__suppliers[supplier_id].goods_amount = amount

            self.__suppliers_amount += 1
            new_supplier = Supplier(prev_amount - amount, self.__suppliers_amount - 1)
            self.__suppliers = np.append(self.__suppliers, new_supplier)
            new_line = np.empty((1, self.__consumers_amount), dtype=Root)

            for i in range(0, self.__consumers_amount):
                new_line[0][i] = Root(0 if i != consumer_id else M_VAL, new_supplier, self.consumers[i])
            self.__price_matrix = np.concatenate((self.price_matrix, new_line), axis=0)

    def __remove_additional_restriction(self, supplier_id: int, consumer_id: int, action: str, amount: int | float):
        root = self.price_matrix[supplier_id][consumer_id]
        if action == '>':
            root.supplier.real_amount += amount
            root.supplier.goods_amount += amount
            root.consumer.real_amount += amount
            root.consumer.goods_amount += amount

            solution_root = self.__solution[supplier_id][consumer_id]
            solution_root.amount += amount
            solution_root.repr = create_eps_expression(solution_root.epsilon, solution_root.amount)
        else:
            final_amount = self.__suppliers[supplier_id].real_amount + self.__suppliers[-1].real_amount
            self.suppliers[supplier_id].real_amount = final_amount
            self.suppliers[supplier_id].goods_amount = final_amount

            for i in range(0, self.__consumers_amount):
                solution_root = self.__solution[supplier_id][i]
                solution_root.amount += self.__solution[-1][i].amount
                solution_root.epsilon += self.__solution[-1][i].epsilon
                solution_root.repr = create_eps_expression(solution_root.epsilon, solution_root.amount)

            self.__suppliers_amount -= 1
            self.__suppliers = np.delete(self.suppliers, -1)
            self.__solution = self.__solution = np.delete(self.__solution, -1, axis=0)

    def __extend_transport_matrix(self) -> None:
        consumers, suppliers = self.__get_disbalanced_participants()
        self.__consumers_amount += 1
        new_consumer = Consumer(sum(item[0] for item in consumers.values()), self.__consumers_amount - 1,
                                sum(item[1] for item in consumers.values()))
        self.__consumers = np.append(self.__consumers, new_consumer)
        new_consumer_line = np.empty((self.__suppliers_amount, 1), dtype=Root)
        for i in range(self.__suppliers_amount):
            new_consumer_line[i][0] = Root(M_VAL, self.suppliers[i], new_consumer,
                                           amount=consumers[i][0] if i in consumers else 0,
                                           epsilon=consumers[i][1] if i in consumers else 0,
                                           representation=str(consumers[i][0]) if i in consumers else '0',
                                           capacity=M_VAL)
        self.__price_matrix = np.concatenate((self.__price_matrix, new_consumer_line), axis=1)

        self.__suppliers_amount += 1
        new_supplier = Supplier(sum(item[0] for item in suppliers.values()), self.__suppliers_amount - 1,
                                sum(item[1] for item in suppliers.values()))
        self.__suppliers = np.append(self.__suppliers, new_supplier)
        new_supplier_line = np.empty((1, self.__consumers_amount), dtype=Root)
        for i in range(self.__consumers_amount):
            new_supplier_line[0][i] = Root(M_VAL if i != self.__consumers_amount - 1 else 0,
                                           new_supplier, self.consumers[i],
                                           amount=suppliers[i][0] if i in suppliers else 0,
                                           epsilon=suppliers[i][1] if i in suppliers else 0,
                                           representation=str(suppliers[i][0]) if i in suppliers else '0',
                                           capacity=M_VAL)
        self.__price_matrix = np.concatenate((self.price_matrix, new_supplier_line), axis=0)

        self.__basic_plan = np.concatenate((self.__basic_plan, new_consumer_line), axis=1)
        self.__basic_plan = np.concatenate((self.__basic_plan, new_supplier_line), axis=0)

    def __collapse_transport_matrix(self):
        self.__solution = self.__solution[:-1, :-1]
        self.__price_matrix = self.price_matrix[:-1, :-1]
        self.__suppliers = self.suppliers[:-1]
        self.__consumers = self.consumers[:-1]
        self.__suppliers_amount -= 1
        self.__consumers_amount -= 1

    def __solve_extended_transport_matrix(self):
        self.__solution = np.zeros((self.__suppliers_amount, self.__consumers_amount), dtype=Root)
        for supplier_id in range(self.__suppliers_amount):
            for consumer_id in range(self.__consumers_amount):
                self.__solution[supplier_id][consumer_id] = copy.copy(self.latest_basic_plan[supplier_id][consumer_id])

        used_plans = []
        while True:
            basic_plan_cells = []
            reserve_cells = []
            for supplier_row in self.__solution:
                for root in supplier_row:
                    if 0 < root.amount < root.capacity:
                        basic_plan_cells.append(root)
                    elif root.amount in (0, root.capacity):
                        reserve_cells.append(root)
            acyclic_cells, other_cells = find_acyclic_plan(basic_plan_cells, reserve_cells, self.__suppliers_amount,
                                                           self.__consumers_amount,  used_plans)

            supplier_values, consumer_values = self.__fill_conditional_values(acyclic_cells)

            potentials = self.__calculate_potentials(supplier_values, consumer_values, other_cells)
            d_values = np.array([val for key, val in potentials.items() if key[2] == 'd'])
            c_values = np.array([val for key, val in potentials.items() if key[2] == 'c'])

            if np.any(d_values > 0) or np.any(c_values < 0):
                if np.any(c_values < 0):
                    min_potential = sorted([(key, val) for key, val in potentials.items() if key[2] == 'c'],
                                           key=lambda x: x[1])[0]
                else:
                    min_potential = sorted([(key, val) for key, val in potentials.items() if key[2] == 'd'],
                                           key=lambda x: x[1])[0]

                loop = self.__find_potential_loop(min_potential, acyclic_cells)
                if not loop:
                    continue
                amount = self.__find_min_loop_capacity_value(loop)

                if amount != 0:
                    self.__transportation_redistribution(loop, int(amount), epsilon=0)
            else:
                break

            consumer_exp = create_eps_expression(self.consumers[-1].real_epsilon, self.consumers[-1].real_amount)
            supplier_epx = create_eps_expression(self.suppliers[-1].real_epsilon, self.suppliers[-1].real_amount)
            if self.__solution[-1][-1].repr == consumer_exp == supplier_epx:
                self.__collapse_transport_matrix()

    def __create_transition_matrix(self, matrix: npt.NDArray[Root]) -> List[Dict[str, int | float]]:
        transition_roots = []
        for supplier_idx, line in enumerate(matrix):
            for consumer_idx, item in enumerate(line):
                if item.repr != '0':
                    transition_root = {
                        'supplier_id': supplier_idx,
                        'consumer_id': consumer_idx,
                        'amount': item.amount,
                        'epsilon': item.epsilon
                    }
                    transition_roots.append(transition_root)
        return transition_roots

    def get_optimal_solution_price(self) -> int | float:
        price = 0
        for i in range(len(self.__solution)):
            for root in self.__solution[i]:
                price += root.amount * root.price
        return price

    def create_basic_plan(self, mode: int=1) -> tuple[List[Dict[str, int | float]], int | float]:
        res = self.check_table_balance()
        if not res:
            self.__make_table_balanced()

        if self.__restrictions:
            for cell, restriction in self.__restrictions.items():
                self.__put_additional_restriction(cell[0], cell[1], restriction[0], restriction[1])

        if mode == 1:
            basic_plan = self.__north_western_method()
        elif mode == 2:
            basic_plan = self.__minimum_cost_method()
        else:
            basic_plan = self.__vogel_method()

        transition_matrix = self.__create_transition_matrix(basic_plan[0])
        self.__restore_price_matrix_values()
        return transition_matrix, basic_plan[1]

    def create_optimal_plan(self) -> Optional[tuple[List[Dict[str, int | float]], int | float]]:
        self.__solution = np.zeros((self.__suppliers_amount, self.__consumers_amount), dtype=Root)
        for supplier_id in range(self.__suppliers_amount):
            for consumer_id in range(self.__consumers_amount):
                self.__solution[supplier_id][consumer_id] = copy.copy(self.latest_basic_plan[supplier_id][consumer_id])

        while True:
            supplier_values, consumer_values = self.__fill_conditional_values()
            potentials = self.__calculate_potentials(supplier_values, consumer_values)
            values = np.array([*potentials.values()])
            if np.any(values < 0):
                min_potential = sorted(potentials.items(), key=lambda x: x[1])[0]
                loop = self.__find_potential_loop(min_potential)
                if not loop:
                    return None
                amount, epsilon = self.__find_min_loop_value(loop)
                self.__transportation_redistribution(loop, amount, epsilon)
            else:
                break
        for cell, restriction in self.__restrictions.items():
            self.__remove_additional_restriction(cell[0], cell[1], restriction[0], restriction[1])

        price = self.get_optimal_solution_price()
        transition_matrix = self.__create_transition_matrix(self.__solution)
        return transition_matrix, price

    def solve_capacity_plan(self) -> Optional[tuple[List[Dict[str, int | float]], int | float]]:
        self.__minimum_cost_method()

        if self.__check_balance_equations() is False:
            self.__extend_transport_matrix()
            self.__solve_extended_transport_matrix()
        else:
            self.create_optimal_plan()

        price = self.get_optimal_solution_price()
        transition_matrix = self.__create_transition_matrix(self.__solution)
        return transition_matrix, price

    @property
    def price_matrix(self):
        return self.__price_matrix

    @property
    def consumers(self):
        return self.__consumers

    @property
    def suppliers(self):
        return self.__suppliers

    @property
    def latest_basic_plan(self):
        return self.__basic_plan

    @property
    def latest_optimal_plan(self):
        return self.__solution

    @property
    def has_capacities(self):
        return self.__capacities is not None
