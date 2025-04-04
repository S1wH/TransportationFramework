from backend.transportation_lib.transport_table import TransportTable
import numpy as np


t1 = TransportTable(
    [1, 1, 1],
    [1, 1, 1],
    np.array([
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]
    ], dtype=np.float16)
)

solution, price = t1.create_basic_plan(3)
print(solution)

# suppliers = [10, 20]  # Поставщики
# consumers = [15, 15]  # Потребители
# price_matrix = np.array([[1, 2], [3, 4]], dtype=np.float16)  # Стоимости
#
# table = TransportTable(suppliers, consumers, price_matrix)
# basic_plan, cost = table.create_basic_plan(mode=3)  # mode=3 вызывает __fogel_method
#
# print("Базисный план:")
# for item in basic_plan:
#     print(f"Поставщик {item['supplier_id'] + 1} -> Потребитель {item['consumer_id'] + 1}: {item['amount']}")
# print(f"Общая стоимость: {cost}")
