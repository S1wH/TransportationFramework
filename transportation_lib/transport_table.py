from .transport_errors import MatrixDimensionError, InvalidPriceValueError, InvalidAmountGood
from .utils import delete_roots


class TransportTable:
    def __init__(self, suppliers_amount: int, consumers_amount: int, suppliers: list[float | int],
                 consumers: list[float | int], price_matrix: list[list[float | int]]):
        self.__validate_table(suppliers_amount, consumers_amount, suppliers, consumers, price_matrix)
        self.__suppliers_amount = suppliers_amount
        self.__consumers_amount = consumers_amount
        self.__suppliers = suppliers
        self.__consumers = consumers
        self.__price_dict = {}
        self.__price_matrix = price_matrix
        for supplier_id, prices in enumerate(price_matrix):
            for consumer_id, price in enumerate(prices):
                self.__price_dict[(supplier_id, consumer_id)] = price

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

    def __validate_table(self, suppliers_amount: int, consumers_amount: int, suppliers: list[float | int],
                         consumers: list[float | int], price_matrix: list[list[float | int]]) -> None:
        if suppliers_amount != len(suppliers):
            raise MatrixDimensionError(suppliers_amount, len(suppliers))
        if suppliers_amount != len(price_matrix):
            raise MatrixDimensionError(suppliers_amount, len(price_matrix))
        if consumers_amount != len(consumers):
            raise MatrixDimensionError(consumers_amount, len(consumers))
        for supplier_id, supplier in enumerate(suppliers):
            if not isinstance(supplier, (int, float)) or supplier <= 0:
                raise InvalidAmountGood(supplier, 0, supplier_id)
        for consumer_id, consumer in enumerate(consumers):
            if not isinstance(consumer, (int, float)) or consumer <= 0:
                raise InvalidAmountGood(consumer, 1, consumer_id)
        for supplier_id, prices in enumerate(price_matrix, 1):
            if len(prices) != consumers_amount:
                raise MatrixDimensionError(consumers_amount, len(prices))
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
            for idx, supplier in enumerate(self.__price_matrix):
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
        price = 0
        while consumer_id != self.__consumers_amount or supplier_id != self.__suppliers_amount:
            good_amount = min(cur_consumer, cur_supplier)
            solution[supplier_id][consumer_id] = good_amount
            price += self.price_matrix[supplier_id][consumer_id] * good_amount
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
        return solution, price

    def __minimum_cost_method(self) -> tuple[list[list[float | int]], int | float]:
        suppliers = self.suppliers.copy()
        consumers = self.consumers.copy()
        solution = [[0] * self.__consumers_amount for _ in range(self.__suppliers_amount)]
        counter = 0
        price = 0
        price_dict = sorted(self.__price_dict.items(), key=lambda x: x[1])
        while counter != self.__consumers_amount + self.__suppliers_amount - 1:
            min_cell_supplier = price_dict[0][0][0]
            min_cell_consumer = price_dict[0][0][1]
            good_amount = min(suppliers[min_cell_supplier], consumers[min_cell_consumer])
            price += price_dict[0][1] * good_amount
            if suppliers[min_cell_supplier] > consumers[min_cell_consumer]:
                suppliers[min_cell_supplier] -= good_amount
                price_dict = delete_roots(price_dict, 1, min_cell_consumer)
            elif suppliers[min_cell_supplier] < consumers[min_cell_consumer]:
                consumers[min_cell_consumer] -= good_amount
                delete_roots(price_dict, 0, min_cell_supplier)
            solution[min_cell_supplier][min_cell_consumer] = good_amount
            counter += 1
        return solution, price

    def create_basic_plan(self, mode: int=1):
        if self.check_table_balance() is False:
            self.__make_table_balanced()
        if mode == 1:
            basic_plan = self.__north_western_method()
        elif mode == 2:
            basic_plan = self.__minimum_cost_method()
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
