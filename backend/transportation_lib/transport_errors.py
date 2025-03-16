from typing import Any


class InvalidMatrixDimension(Exception):
    def __init__(self, amount: int, length: int) -> None:
        self.__amount = amount
        self.__length = length

    def __str__(self) -> str:
        return f'Переданная размерность {self.__amount} не соответствует переданному количеству {self.__length}'


class InvalidPriceValueError(Exception):
    def __init__(self, price: Any, position: tuple[int, int]) -> None:
        self.__price = price
        self.__supplier_pos = position[0]
        self.__consumer_pos = position[1]

    def __str__(self) -> str:
        return (f'Переданная стоимость перевозки {self.__price} от поставщика {self.__supplier_pos}'
                f' к потребителю {self.__consumer_pos} некорректна')


class InvalidAmountGood(Exception):
    def __init__(self, val: Any, good_type: int, position: int) -> None:
        self.__amount = val
        self.__good_type = 'Поставщик' if good_type == 0 else 'Потребитель'
        self.__position = position

    def __str__(self) -> str:
        return (f'{self.__good_type} {self.__position}'
                f' обладает некорректной потребностью/запасом продукта {self.__amount}')


class InvalidRestrictionIndices(Exception):
    def __init__(self, restriction_indices: tuple[int, int], matrix_dimension: tuple[int, int]) -> None:
        self.__indices = (restriction_indices[0] + 1, restriction_indices[1] + 1)
        self.__matrix_dimension = matrix_dimension

    def __str__(self) -> str:
        return f'Некорректная позиция ограничения {self.__indices} для матрицы размерностью {self.__matrix_dimension}'


class InvalidRestrictionSymbol(Exception):
    def __init__(self, symbol: str) -> None:
        self.__symbol = symbol

    def __str__(self) -> str:
        return f'Некорректный символ ограничения {self.__symbol}'


class InvalidRestrictionValue(Exception):
    def __init__(self, value: int | float, value_borders: tuple[int, int | float]) -> None:
        self.__value = value
        self.__value_borders = value_borders

    def __str__(self) -> str:
        return f'Численное значение ограничения {self.__value} выходит за допустимые границы {self.__value_borders}'


class InvalidCapacitiesDimension(Exception):
    def __init__(self, capacities_shape: tuple[int], matrix_shape: tuple[int]) -> None:
        self.__capacities_shape = capacities_shape
        self.__matrix_shape = matrix_shape

    def __str__(self) -> str:
        return (f'Переданная размерность для пропускных способностей {self.__capacities_shape}'
                f' не соответствует переданной размерности матрицы {self.__matrix_shape}')


class InvalidCapacityValue(Exception):
    def __init__(self, value: int | float, line_value: int | float, line_num: int, line_type: int) -> None:
        self.__value = value
        self.__line_value = line_value
        self.__line_num = line_num
        self.__line_type = 'Строка' if line_type == 0 else 'Столбец'

    def __str__(self) -> str:
        return (f'{self.__line_type} №{self.__line_num} имеет значение ({self.__line_value}) больше,'
                f' чем пропускная способность {self.__value}')
