def delete_roots(roots: list[tuple[tuple[int, int], int]], pos: int, value: int) -> list[tuple[tuple[int, int], int]]:
    for _, root in enumerate(roots.copy()):
        if root[0][pos] == value:
            roots.remove(root)
    return roots


def find_line_penalty(line: list[int | float], baned_roots: list[int]):
    line = [root for idx, root in enumerate(line) if idx not in baned_roots]
    line.sort()
    return abs(line[0] - line[1]) if len(line) > 1 else line[0]


def update_root_values(suppliers, consumers, min_cell_consumer, min_cell_supplier, price_dict, solution):
    good_amount = min(suppliers[min_cell_supplier], consumers[min_cell_consumer])
    price = price_dict[0][1] * good_amount
    if suppliers[min_cell_supplier] > consumers[min_cell_consumer]:
        suppliers[min_cell_supplier] -= good_amount
        delete_roots(price_dict, 1, min_cell_consumer)
    elif suppliers[min_cell_supplier] < consumers[min_cell_consumer]:
        consumers[min_cell_consumer] -= good_amount
        delete_roots(price_dict, 0, min_cell_supplier)
    solution[min_cell_supplier][min_cell_consumer] = good_amount
    return price, good_amount
