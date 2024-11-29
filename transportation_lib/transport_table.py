from .transport_errors import MatrixDimensionError, InvalidPriceValueError, InvalidAmountGood


class TransportTable:
    def __init__(self, suppliers_amount: int, consumers_amount: int, suppliers: list[float], consumers: list[float],
                 price_matrix: list[list[float]]):
        self.__validate_table(suppliers_amount, consumers_amount, suppliers, consumers, price_matrix)
        self.__suppliers_amount = suppliers_amount
        self.__consumers_amount = consumers_amount
        self.__suppliers = suppliers
        self.__consumers = consumers
        self.__price_matrix = price_matrix

    def pprint(self):
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

    def pprint_res(self, solution: list[list[int]]):
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

    def check_table_balance(self):
        return sum(self.suppliers) == sum(self.consumers)

    def __validate_table(self, suppliers_amount: int, consumers_amount: int, suppliers: list[float],
                         consumers: list[float], price_matrix: list[list[float]]):
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

    def __make_table_balanced(self):
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

    def __north_western_method(self):
        solution = [[0] * self.__consumers_amount for _ in range(self.__suppliers_amount)]
        consumer_id = 0
        cur_consumer = self.consumers[consumer_id]
        supplier_id = 0
        cur_supplier = self.suppliers[supplier_id]
        while consumer_id != self.__consumers_amount or supplier_id != self.__suppliers_amount:
            good_amount = min(cur_consumer, cur_supplier)
            solution[supplier_id][consumer_id] = good_amount
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
        self.pprint_res(solution)

    def create_basic_plan(self, mode: int=0):
        if self.check_table_balance() is False:
            self.__make_table_balanced()
        self.pprint()
        if mode == 1:
            self.__north_western_method()


    @property
    def price_matrix(self):
        return self.__price_matrix

    @property
    def consumers(self):
        return self.__consumers

    @property
    def suppliers(self):
        return self.__suppliers
