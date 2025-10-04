from __future__ import annotations

import random
from typing import Optional

from .api import Grid, count_solutions, is_valid, solve


def _empty_grid() -> Grid:
    return [[0] * 9 for _ in range(9)]


def _random_full_solution(seed: Optional[int]) -> Grid:
    """Produce a full valid solution by solving an empty grid with a randomized search order."""
    rng = random.Random(seed)
    grid = _empty_grid()
    attempts = 0
    while attempts < 30:
        r = rng.randrange(9)
        c = rng.randrange(9)
        if grid[r][c] != 0:
            attempts += 1
            continue
        values = list(range(1, 10))
        rng.shuffle(values)
        placed = False
        for value in values:
            grid[r][c] = value
            if is_valid(grid) and solve(grid) is not None:
                placed = True
                break
            grid[r][c] = 0
        if not placed:
            grid[r][c] = 0
        attempts += 1
    result = solve(grid)
    if result is None:
        raise RuntimeError("Failed to construct a full solution")
    return result.grid


def generate(seed: Optional[int] = None, *, target_givens: int = 28) -> Grid:
    """Create a Sudoku puzzle while preserving unique solvability."""
    rng = random.Random(seed)
    full = _random_full_solution(seed)
    puzzle = [row[:] for row in full]
    cells = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(cells)
    for r, c in cells:
        givens = sum(1 for rr in range(9) for cc in range(9) if puzzle[rr][cc] != 0)
        if givens <= target_givens:
            break
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        if count_solutions(puzzle, limit=2) != 1:
            puzzle[r][c] = backup
    return puzzle


__all__ = ["generate"]
