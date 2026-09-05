from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .solver import BitDLX, grid_clues

Grid = List[List[int]]


def build_ec_rows_from_grid(grid: Grid) -> Grid:
    """Return a defensive grid copy used by the compatibility engine."""
    return [row[:] for row in grid]


def apply_solution_to_grid(grid: Grid, sol_rows: List[Tuple[int, int, int]]) -> None:
    for r, c, d in sol_rows:
        grid[r][c] = d + 1


@dataclass
class Column:
    name: Optional[int] = None


class DLXEngine:
    """
    Compatibility shim over the bitset exact-cover engine.

    Each compatibility engine owns its BitDLX instance. This keeps public API
    calls reentrant and prevents search statistics from leaking across callers.
    """

    def __init__(self) -> None:
        self.header = Column()
        self.nodes = 0
        self.branches = 0
        self.backtracks = 0
        self.max_depth = 0
        self._solver = BitDLX()

    def _sync_stats(self) -> None:
        stats = self._solver.stats
        self.nodes = stats.nodes
        self.branches = stats.branches
        self.backtracks = stats.backtracks
        self.max_depth = stats.max_depth

    def solve_first(self, rows: Grid) -> Optional[List[Tuple[int, int, int]]]:
        count, solved = self._solver.count_solutions(grid_clues(rows), limit=1)
        self._sync_stats()
        if count == 0 or solved is None:
            return None
        return [(r, c, solved[r][c] - 1) for r in range(9) for c in range(9)]

    def count(self, rows: Grid, limit: int = 2) -> int:
        count, _ = self._solver.count_solutions(grid_clues(rows), limit=limit)
        self._sync_stats()
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
