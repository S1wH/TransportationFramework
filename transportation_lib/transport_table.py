import operator
from .transport_errors import MatrixDimensionError, InvalidPriceValueError, InvalidAmountGood
from .utils import find_line_penalty, update_root_values


class TransportTable:
    def __init__(self, suppliers: list[float | int], consumers: list[float | int],
                 price_matrix: list[list[float | int]]):
        self.__validate_table(suppliers, consumers, price_matrix)
        self.__suppliers_amount = len(suppliers)
        self.__consumers_amount = len(consumers)
        self.__suppliers = suppliers
        self.__consumers = consumers
        self.__price_dict = {}
        self.__price_matrix = price_matrix
        for supplier_id, prices in enumerate(price_matrix):
            for consumer_id, price in enumerate(prices):
                self.__price_dict[(supplier_id, consumer_id)] = price
        self.__solution = [[0] * self.__consumers_amount for _ in range(self.__suppliers_amount)]

    def pprint(self) -> None:
        print('', end='\t')
        for i in range(len(self.price_matrix[0])):
            print(f'T{i + 1}', end='\t')
        print('A')
        for i in range(len(self.price_matrix)):
            print(f'S{i + 1}', end='\t')
            for j in range(len(self.price_matrix[i])):
                print(self.price_matrix[i][j], end='\t')
            print(self.suppliers[i])
        print('B', end='\t')
        for i in range(len(self.consumers)):
            print(self.consumers[i], end='\t')
        print('\n')

    def pprint_res(self, solution: list[list[int | float]]) -> None:
        print('', end='\t')
        for i in range(len(self.price_matrix[0])):
            print(f'T{i + 1}', end='\t')
        print('A')
        for i in range(len(solution)):
            print(f'S{i + 1}', end='\t')
            for j in range(len(solution[i])):
                print(solution[i][j], end='\t')
            print(self.suppliers[i])
        print('B', end='\t')
        for i in range(len(self.consumers)):
            print(self.consumers[i], end='\t')
        print('\n')

    def check_table_balance(self) -> bool:
        return sum(self.suppliers) == sum(self.consumers)

    def __validate_table(self, suppliers: list[float | int], consumers: list[float | int],
                         price_matrix: list[list[float | int]]) -> None:
        for supplier_id, supplier in enumerate(suppliers):
            if not isinstance(supplier, (int, float)) or supplier <= 0:
                raise InvalidAmountGood(supplier, 0, supplier_id)
        for consumer_id, consumer in enumerate(consumers):
            if not isinstance(consumer, (int, float)) or consumer <= 0:
                raise InvalidAmountGood(consumer, 1, consumer_id)
        for supplier_id, prices in enumerate(price_matrix, 1):
            if len(prices) != len(consumers):
                raise MatrixDimensionError(len(consumers), len(prices))
            for consumer_id, price in enumerate(prices, 1):
                if not isinstance(price, (int, float)) or price < 0:
                    raise InvalidPriceValueError(price, (supplier_id, consumer_id))

    def __make_table_balanced(self) -> None:
        total_suppliers_goods = sum(self.suppliers)
        total_consumers_goods = sum(self.consumers)
        abs_difference = abs(total_suppliers_goods - total_consumers_goods)
        if total_suppliers_goods > total_consumers_goods:
            self.__consumers_amount += 1
            self.__consumers.append(abs_difference)
            for idx, _ in enumerate(self.__price_matrix):
                self.__price_matrix[idx].append(0)
        else:
            self.__suppliers_amount += 1
            self.__suppliers.append(abs_difference)
            self.__price_matrix.append([0] * self.__consumers_amount)

    def __north_western_method(self) -> tuple[list[list[float | int]], int | float]:
        solution = [[0] * self.__consumers_amount for _ in range(self.__suppliers_amount)]
        consumer_id = 0
        cur_consumer = self.consumers[consumer_id]
        supplier_id = 0
        cur_supplier = self.suppliers[supplier_id]
        cost = 0
        while consumer_id != self.__consumers_amount or supplier_id != self.__suppliers_amount:
            good_amount = min(cur_consumer, cur_supplier)
            solution[supplier_id][consumer_id] = good_amount
            cost += self.price_matrix[supplier_id][consumer_id] * good_amount
            if cur_consumer < cur_supplier:
                cur_supplier -= good_amount
                consumer_id += 1
                cur_consumer = self.consumers[consumer_id]
            elif cur_consumer > cur_supplier:
                cur_consumer -= good_amount
                supplier_id += 1
                cur_supplier = self.suppliers[supplier_id]
            else:
                supplier_id += 1
                consumer_id += 1
                cur_consumer = self.consumers[consumer_id] if consumer_id != self.__consumers_amount else None
                cur_supplier = self.suppliers[supplier_id] if supplier_id != self.__suppliers_amount else None
        return solution, cost

    def __minimum_cost_method(self) -> tuple[list[list[float | int]], int | float]:
        suppliers = self.suppliers.copy()
        consumers = self.consumers.copy()
        counter = 0
        cost = 0
        price_dict = sorted(self.__price_dict.copy().items(), key=lambda x: x[1])
        while counter != self.__consumers_amount + self.__suppliers_amount - 1:
            min_cell_supplier = price_dict[0][0][0]
            min_cell_consumer = price_dict[0][0][1]
            price, good_amount = update_root_values(suppliers, consumers, price_dict, self.__solution)
            cost += price
            self.__solution[min_cell_supplier][min_cell_consumer] = good_amount
            counter += 1
        return self.__solution, cost

    def __fogel_method(self) -> tuple[list[list[float | int]], int | float]:
        cost = 0
        counter = 0
        suppliers = self.suppliers.copy()
        consumers = self.consumers.copy()
        suppliers_list = list(self.price_matrix)
        consumers_list = [list(consumer_column) for consumer_column in zip(*self.price_matrix)]
        baned_suppliers = []
        baned_consumers = []
        while counter != self.__consumers_amount + self.__suppliers_amount - 1:
            suppliers_penalties = {supplier: find_line_penalty(prices.copy(), baned_consumers) for supplier, prices
                                   in enumerate(suppliers_list.copy()) if supplier not in baned_suppliers}
            consumers_penalties = {consumer: find_line_penalty(prices.copy(), baned_suppliers) for consumer, prices
                                   in enumerate(consumers_list.copy()) if consumer not in baned_consumers}
            max_supplier_penalty = max(suppliers_penalties.items(), key=operator.itemgetter(1))
            max_consumer_penalty = max(consumers_penalties.items(), key=operator.itemgetter(1))

            consumer_idx = 0
            supplier_idx = 0
            if max_supplier_penalty[1] > max_consumer_penalty[1]:
                supplier_idx = max_supplier_penalty[0]
                consumer_idx = suppliers_list[supplier_idx].index(
                    min(item for idx, item in enumerate(suppliers_list[supplier_idx]) if idx not in baned_consumers))
            elif max_supplier_penalty[1] <= max_consumer_penalty[1]:
                consumer_idx = max_consumer_penalty[0]
                supplier_idx = consumers_list[consumer_idx].index(
                    min(item for idx, item in enumerate(consumers_list[consumer_idx]) if idx not in baned_suppliers))

            goods_amount = min(suppliers[supplier_idx], consumers[consumer_idx])
            cost += suppliers_list[supplier_idx][consumer_idx] * goods_amount
            if suppliers[supplier_idx] > consumers[consumer_idx]:
                baned_consumers.append(consumer_idx)
                suppliers[supplier_idx] -= goods_amount
            elif suppliers[supplier_idx] < consumers[consumer_idx]:
                baned_suppliers.append(supplier_idx)
                consumers[consumer_idx] -= goods_amount
            self.__solution[supplier_idx][consumer_idx] = goods_amount
            # TODO: epsilon modified version
            counter += 1
        return self.__solution, cost

    def create_basic_plan(self, mode: int=1):
        if self.check_table_balance() is False:
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
