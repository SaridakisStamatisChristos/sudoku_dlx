from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .solver import SOLVER, grid_clues

Grid = List[List[int]]


def build_ec_rows_from_grid(grid: Grid) -> Grid:
    """Return a copy of the grid used by the compatibility engine."""
    return [row[:] for row in grid]


def apply_solution_to_grid(grid: Grid, sol_rows: List[Tuple[int, int, int]]) -> None:
    for r, c, d in sol_rows:
        grid[r][c] = d + 1


@dataclass
class Column:
    name: Optional[int] = None


class DLXEngine:
    """Compatibility shim over the legacy bitset solver."""

    def __init__(self) -> None:
        self.header = Column()
        self.nodes = 0
        self.backtracks = 0

    def solve_first(self, rows: Grid) -> Optional[List[Tuple[int, int, int]]]:
        count, solved = SOLVER.count_solutions(grid_clues(rows), limit=1)
        self.nodes = SOLVER.stats.nodes
        # Approximate backtracks using branches statistic when available
        branches = getattr(SOLVER.stats, "branches", 0)
        self.backtracks = max(branches - count, 0)
        if count == 0 or solved is None:
            return None
        return [(r, c, solved[r][c] - 1) for r in range(9) for c in range(9)]

    def count(self, rows: Grid, limit: int = 2) -> int:
        count, _ = SOLVER.count_solutions(grid_clues(rows), limit=limit)
        self.nodes = SOLVER.stats.nodes
        branches = getattr(SOLVER.stats, "branches", 0)
        self.backtracks = max(branches - count, 0)
        return count


def randomized_digits(seed: Optional[int]) -> List[int]:
    rng = random.Random(seed)
    digits = list(range(9))
    rng.shuffle(digits)
    return digits


__all__ = [
    "Grid",
    "DLXEngine",
    "build_ec_rows_from_grid",
    "apply_solution_to_grid",
    "randomized_digits",
]
