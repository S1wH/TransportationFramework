from typing import Any


class MatrixDimensionError(Exception):
    def __init__(self, amount: int, length: int):
        self.__amount = amount
        self.__length = length

    def __str__(self):
        return f'Переданная размерность {self.__amount} не соответствует переданному количеству {self.__length}'


class InvalidPriceValueError(Exception):
    def __init__(self, price: Any, position: tuple[int, int]):
        self.__price = price
        self.__supplier_pos = position[0]
        self.__consumer_pos = position[1]

    def __str__(self):
        return (f'Переданная стоимость перевозки {self.__price} от поставщика {self.__supplier_pos}'
                f' к потребителю {self.__consumer_pos} некорректна')


class InvalidAmountGood(Exception):
    def __init__(self, val: Any, good_type: int, position: int):
        self.__amount = val
        self.__good_type = 'Поставщик' if good_type == 0 else 'Потребитель'
        self.__position = position

    def __str__(self):
        return (f'{self.__good_type} {self.__position}'
                f' обладает некорректной потребностью/запасом продукта {self.__amount}')
