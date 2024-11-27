from transport_errors import MatrixDimensionError, InvalidPriceValueError


class TransportTable:
    def __init__(self, suppliers_amount: int, consumers_amount: int, suppliers: list[float], consumers: list[float],
                 price_matrix: list[list[float]]):
        self.__validate_table(suppliers_amount, consumers_amount, suppliers, consumers, price_matrix)
        self.__suppliers = suppliers
        self.__consumers = consumers

    def __validate_table(self, suppliers_amount: int, consumers_amount: int, suppliers: list[float],
                         consumers: list[float], price_matrix: list[list[float]]):
        if suppliers_amount != len(suppliers):
            raise MatrixDimensionError(suppliers_amount, len(suppliers))
        if consumers_amount != len(consumers):
            raise MatrixDimensionError(consumers_amount, len(consumers))
        for supplier_id, prices in enumerate(price_matrix, 1):
            for consumer_id, price in enumerate(prices, 1):
                if not isinstance(price, (int, float)):
                    raise InvalidPriceValueError(price, (supplier_id, consumer_id))
