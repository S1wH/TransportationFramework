import operator
from typing import Optional
from abc import ABC
from prettytable import PrettyTable
from .transport_errors import MatrixDimensionError, InvalidPriceValueError, InvalidAmountGood
from .utils import *


class Participant(ABC):
    def __init__(self, goods_amount: int | float, obj_id: int, epsilon: int = 0) -> None:
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


class Consumer(Participant):
    pass


class Supplier(Participant):
    pass


class Root:
    def __init__(self, price: int | float, supplier: Supplier, consumer: Consumer, epsilon: int=None) -> None:
        self.price = price
        self.epsilon = epsilon
        self.supplier = supplier
        self.consumer = consumer

    def __lt__(self, other):
        return self.price < other.price

    def __le__(self, other):
        return self.price < other.price

    def __gt__(self, other):
        return self.price > other.price

    def __ge__(self, other):
        return self.price >= other.price

    def __eq__(self, other):
        return self.price == other.price


class TransportTable:
    def __init__(self, suppliers: list[float | int], consumers: list[float | int],
                 price_matrix: list[list[float | int]]) -> None:

        self.__suppliers_amount = len(suppliers)
        self.__consumers_amount = len(consumers)
        self.__suppliers = np.array([Supplier(supplier, supplier_id)
                                     for supplier_id, supplier in enumerate(suppliers)], dtype=Supplier)
        self.__consumers = np.array([Consumer(consumer, consumer_id)
                                     for consumer_id, consumer in enumerate(consumers)], dtype=Consumer)
        self.__price_matrix = np.zeros((self.__suppliers_amount, self.__consumers_amount), dtype=Root)
        for supplier_id, prices in enumerate(price_matrix):
            for consumer_id, price in enumerate(prices):
                supplier = self.__suppliers[supplier_id]
                consumer = self.__consumers[consumer_id]
                self.__price_matrix[supplier_id][consumer_id] = Root(price, supplier, consumer)

        self.__validate_table()
        self.__solution = np.zeros((self.__suppliers_amount, self.__consumers_amount), dtype=str)

    def pprint(self) -> None:
        table = PrettyTable([''] + [f'T{i + 1}' for i in range(self.price_matrix[0].size)] + ['A'])
        for i in range(self.price_matrix.shape[0]):
            row = [f'S{i + 1}']
            for j in range(self.price_matrix[i].size):
                row.append(self.price_matrix[i][j].price)
            row.append(create_eps_expression(self.suppliers[i].real_epsilon, self.suppliers[i].real_amount))
            table.add_row(row)
        row = ['B']
        for i in range(self.consumers.size):
            row.append(create_eps_expression(self.consumers[i].real_epsilon, self.consumers[i].real_amount))
        row.append('')
        table.add_row(row)
        print(table)

    def pprint_res(self, solution: npt.NDArray[npt.NDArray[np.float64]]) -> None:
        table = PrettyTable([''] + [f'T{i + 1}' for i in range(self.price_matrix[0].size)] + ['A'])
        for i in range(len(solution)):
            row = [f'S{i + 1}']
            for j in range(len(solution[i])):
                row.append(solution[i][j])
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
                               root.supplier.epsilon):
                return root

    def __validate_table(self) -> None:
        for supplier_id, supplier in enumerate(self.suppliers):
            if not isinstance(supplier.goods_amount, (int, float)) or supplier <= 0:
                raise InvalidAmountGood(supplier, 0, supplier_id)
        for consumer_id, consumer in enumerate(self.consumers):
            if not isinstance(consumer.goods_amount, (int, float)) or consumer <= 0:
                raise InvalidAmountGood(consumer, 1, consumer_id)
        for supplier_id, prices in enumerate(self.price_matrix, 1):
            if len(prices) != self.__consumers_amount:
                raise MatrixDimensionError(self.__consumers_amount, len(prices))
            for consumer_id, root in enumerate(prices, 1):
                if not isinstance(root.price, (int, float)) or root.price < 0:
                    raise InvalidPriceValueError(root.price, (supplier_id, consumer_id))

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
            for i in range(self.__suppliers_amount):
                new_line[0][i] = Root(0, self.suppliers[i], new_supplier)
            self.__price_matrix = np.concatenate((self.price_matrix, new_line), axis=0)

    def __epsilon_modify_table(self) -> None:
        for supplier in self.suppliers:
            supplier.epsilon = 1
            supplier.real_epsilon = 1
        self.consumers[-1].epsilon = self.__suppliers_amount
        self.consumers[-1].real_epsilon = self.__suppliers_amount

    def __north_western_method(self) -> tuple[npt.NDArray[np.float64], int | float]:
        self.__solution = np.full((self.__suppliers_amount, self.__consumers_amount), '0', dtype='U10')
        consumer_id = 0
        supplier_id = 0
        cost = 0
        while consumer_id != self.__consumers_amount or supplier_id != self.__suppliers_amount:
            root = self.price_matrix[supplier_id][consumer_id]
            min_participant = min(root.consumer, root.supplier)
            goods_amount = min_participant.goods_amount
            eps = min_participant.epsilon
            self.__solution[supplier_id][consumer_id] = create_eps_expression(eps, goods_amount)
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
        self.__restore_price_matrix_values()
        return self.__solution, cost

    def __minimum_cost_method(self) -> tuple[npt.NDArray[np.float64], int | float]:
        self.__solution = np.full((self.__suppliers_amount, self.__consumers_amount), '0', dtype='U10')
        counter = 0
        cost = 0
        while counter != self.__consumers_amount + self.__suppliers_amount - 1:
            root = self.__get_min_valid_root()
            if not root:
                self.__restore_price_matrix_values()
                self.__epsilon_modify_table()
                return self.__minimum_cost_method()
            min_participant = min(root.consumer, root.supplier)
            goods_amount = min_participant.goods_amount
            eps = min_participant.epsilon
            cost += root.price * goods_amount

            root.supplier.goods_amount -= goods_amount
            root.consumer.goods_amount -= goods_amount
            if root.consumer == root.supplier:
                eps = min(root.consumer.epsilon, root.supplier.epsilon)
            root.supplier.epsilon -= eps
            root.consumer.epsilon -= eps

            self.__solution[root.supplier.id][root.consumer.id] = create_eps_expression(eps, goods_amount)
            counter += 1
        self.__restore_price_matrix_values()
        return self.__solution, cost

    def __fogel_method(self) -> tuple[npt.NDArray[np.float64], int | float]:
        self.__solution = np.full((self.__suppliers_amount, self.__consumers_amount), '0', dtype='U10')
        cost = 0
        counter = 0
        while counter != self.__consumers_amount + self.__suppliers_amount - 1:
            suppliers_penalties = {supplier_id: find_line_penalty(supplier)
                                   for supplier_id, supplier in enumerate(self.price_matrix)}
            consumers_penalties = {consumer_id: find_line_penalty(consumer)
                                   for consumer_id, consumer in enumerate(self.price_matrix.T)}
            max_supplier_penalty = max(suppliers_penalties.items(), key=operator.itemgetter(1))
            max_consumer_penalty = max(consumers_penalties.items(), key=operator.itemgetter(1))

            consumer_id = 0
            supplier_id = 0
            if max_supplier_penalty[1] > max_consumer_penalty[1]:
                supplier_id = max_supplier_penalty[0]
                _, consumer_id = get_min_line_element(self.price_matrix[supplier_id, :])
            elif max_supplier_penalty[1] <= max_consumer_penalty[1]:
                consumer_id = max_consumer_penalty[0]
                supplier_id, _ = get_min_line_element(self.price_matrix[:, consumer_id])

            if consumer_id is None or supplier_id is None:
                self.__restore_price_matrix_values()
                self.__epsilon_modify_table()
                return self.__fogel_method()

            root = self.price_matrix[supplier_id][consumer_id]
            min_participant = min(root.consumer, root.supplier)
            goods_amount = min_participant.goods_amount
            eps = min_participant.epsilon
            cost += root.price * goods_amount

            root.supplier.goods_amount -= goods_amount
            root.consumer.goods_amount -= goods_amount
            if root.consumer == root.supplier:
                eps = min(root.consumer.epsilon, root.supplier.epsilon)
            root.supplier.epsilon -= eps
            root.consumer.epsilon -= eps

            self.__solution[supplier_id][consumer_id] = create_eps_expression(eps, goods_amount)
            counter += 1
        self.__restore_price_matrix_values()
        return self.__solution, cost

    def create_basic_plan(self, mode: int=1):
        res = self.check_table_balance()
        if not res:
            self.__make_table_balanced()
        basic_plan = None
        if mode == 1:
            basic_plan = self.__north_western_method()
        elif mode == 2:
            basic_plan = self.__minimum_cost_method()
        elif mode == 3:
            basic_plan = self.__fogel_method()
        return basic_plan


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
    def latest_solution(self):
        return self.__solution
