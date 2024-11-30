def delete_roots(roots: list[tuple[tuple[int, int], int]], pos: int, value: int) -> list[tuple[tuple[int, int], int]]:
    for idx, root in enumerate(roots.copy()):
        if root[0][pos] == value:
            roots.remove(root)
    return roots