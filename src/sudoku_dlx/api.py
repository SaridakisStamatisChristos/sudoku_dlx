from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import List, Optional, Dict, Any

Grid = List[List[int]]

ANALYZE_VERSION = "1"


@dataclass
class Stats:
    ms: float
    nodes: int
    backtracks: int


@dataclass
class SolveResult:
    grid: Grid
    stats: Stats


def from_string(s: str) -> Grid:
    """Parse an 81-char string (digits 1-9, or . 0 - _ for blanks) to a 9x9 grid."""
    text = "".join(ch for ch in s if not ch.isspace())
    if len(text) != 81:
        raise ValueError("grid string must be 81 characters")
    out: Grid = [[0] * 9 for _ in range(9)]
    for i, ch in enumerate(text):
        r, c = divmod(i, 9)
        if ch in "0.-_":
            out[r][c] = 0
        elif ch.isdigit():
            value = int(ch)
            if not (1 <= value <= 9):
                raise ValueError("digits must be 1..9")
            out[r][c] = value
        else:
            raise ValueError(f"bad char at {i}: {ch!r}")
    return out


def to_string(grid: Grid) -> str:
    return "".join(str(x) if x != 0 else "." for row in grid for x in row)


def is_valid(grid: Grid) -> bool:
    """Cheap structural validity (no duplicates in row/col/box for existing clues)."""
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = grid[r][c]
            if v == 0:
                continue
            if v in rows[r] or v in cols[c] or v in boxes[(r // 3) * 3 + (c // 3)]:
                return False
            rows[r].add(v)
            cols[c].add(v)
            boxes[(r // 3) * 3 + (c // 3)].add(v)
    return True


def solve(grid: Grid, *, collect_stats: bool = True) -> Optional[SolveResult]:
    """Solve Sudoku via the underlying DLX engine."""
    if not is_valid(grid):
        return None
    from .engine import DLXEngine, apply_solution_to_grid, build_ec_rows_from_grid

    rows = build_ec_rows_from_grid(grid)
    engine = DLXEngine()
    t0 = perf_counter()
    sol_rows = engine.solve_first(rows)
    ms = (perf_counter() - t0) * 1000.0
    if sol_rows is None:
        return None
    solved = [row[:] for row in grid]
    apply_solution_to_grid(solved, sol_rows)
    stats = Stats(ms=ms, nodes=engine.nodes, backtracks=engine.backtracks)
    return SolveResult(solved, stats)


def count_solutions(grid: Grid, limit: int = 2) -> int:
    from .engine import DLXEngine, build_ec_rows_from_grid

    rows = build_ec_rows_from_grid(grid)
    engine = DLXEngine()
    return engine.count(rows, limit=limit)


def analyze(grid: Grid) -> Dict[str, Any]:
    """
    Return a compact analysis dict for a Sudoku grid. Keys:
      - version: schema version string
      - valid: bool (no row/col/box duplicates among givens)
      - givens: int
      - solvable: bool
      - unique: bool (exactly one solution determined via limit=2)
      - difficulty: float in [0,10] (heuristic)
      - canonical: str (81-char canonical form)
      - solution: str | None (81-char solution if solvable)
      - stats: {ms, nodes, backtracks} (0s if unsolvable)
    """
    from .rating import rate
    from .canonical import canonical_form

    givens = sum(1 for r in range(9) for c in range(9) if grid[r][c] != 0)
    valid = is_valid(grid)
    uniq = False
    solv: Optional[SolveResult] = None
    if valid:
        # Uniqueness and solvability
        uniq = count_solutions(grid, limit=2) == 1
        solv = solve(grid)
    solution = None
    ms = nodes = backs = 0
    if solv is not None:
        solution = to_string(solv.grid)
        ms = int(round(solv.stats.ms))
        nodes = int(solv.stats.nodes)
        backs = int(solv.stats.backtracks)
    return {
        "version": ANALYZE_VERSION,
        "valid": valid,
        "givens": givens,
        "solvable": solv is not None,
        "unique": uniq,
        "difficulty": float(rate(grid)),
        "canonical": canonical_form(grid),
        "solution": solution,
        "stats": {"ms": ms, "nodes": nodes, "backtracks": backs},
    }

__all__ = [
    "Grid",
    "Stats",
    "SolveResult",
    "from_string",
    "to_string",
    "is_valid",
    "solve",
    "count_solutions",
    "analyze",
]
