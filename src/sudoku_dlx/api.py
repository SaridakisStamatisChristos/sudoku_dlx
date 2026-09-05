from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, List, Optional

Grid = List[List[int]]

ANALYZE_VERSION = "1"


@dataclass
class Stats:
    ms: float
    nodes: int
    backtracks: int
    branches: int = 0
    max_depth: int = 0


@dataclass
class SolveResult:
    grid: Grid
    stats: Stats


def is_well_formed(grid: object) -> bool:
    """Return whether ``grid`` is exactly 9x9 with integer values in 0..9."""

    if not isinstance(grid, list) or len(grid) != 9:
        return False
    for row in grid:
        if not isinstance(row, list) or len(row) != 9:
            return False
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return False
    return True


def from_string(s: str) -> Grid:
    """Parse an 81-char string (digits 1-9, or . 0 - _ for blanks) to a 9x9 grid."""

    if not isinstance(s, str):
        raise TypeError("grid input must be a string")
    text = "".join(ch for ch in s if not ch.isspace())
    if len(text) != 81:
        raise ValueError("grid string must be 81 characters")
    out: Grid = [[0] * 9 for _ in range(9)]
    for i, ch in enumerate(text):
        r, c = divmod(i, 9)
        if ch in "0.-_":
            out[r][c] = 0
        elif ch in "123456789":
            out[r][c] = int(ch)
        else:
            raise ValueError(f"bad char at {i}: {ch!r}")
    return out


def to_string(grid: Grid) -> str:
    if not is_well_formed(grid):
        raise ValueError("grid must be a 9x9 list of integers in 0..9")
    return "".join(str(x) if x != 0 else "." for row in grid for x in row)


def is_valid(grid: Grid) -> bool:
    """Return whether a well-formed grid has no duplicate row/column/box clues."""

    if not is_well_formed(grid):
        return False
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = grid[r][c]
            if v == 0:
                continue
            box = (r // 3) * 3 + (c // 3)
            if v in rows[r] or v in cols[c] or v in boxes[box]:
                return False
            rows[r].add(v)
            cols[c].add(v)
            boxes[box].add(v)
    return True


def solve(grid: Grid, *, collect_stats: bool = True) -> Optional[SolveResult]:
    """Solve Sudoku via the bitset exact-cover engine."""

    if not is_valid(grid):
        return None
    from .engine import DLXEngine, apply_solution_to_grid, build_ec_rows_from_grid

    rows = build_ec_rows_from_grid(grid)
    engine = DLXEngine()
    t0 = perf_counter()
    sol_rows = engine.solve_first(rows)
    elapsed_ms = (perf_counter() - t0) * 1000.0
    if sol_rows is None:
        return None

    solved = [row[:] for row in grid]
    apply_solution_to_grid(solved, sol_rows)
    if collect_stats:
        stats = Stats(
            ms=elapsed_ms,
            nodes=engine.nodes,
            backtracks=engine.backtracks,
            branches=engine.branches,
            max_depth=engine.max_depth,
        )
    else:
        stats = Stats(ms=0.0, nodes=0, backtracks=0)
    return SolveResult(solved, stats)


def count_solutions(grid: Grid, limit: int = 2) -> int:
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be an integer >= 1")
    if not is_valid(grid):
        return 0

    from .engine import DLXEngine, build_ec_rows_from_grid

    rows = build_ec_rows_from_grid(grid)
    engine = DLXEngine()
    return engine.count(rows, limit=limit)


def build_reveal_trace(initial: Grid, solved: Grid, stats: Stats) -> Dict[str, Any]:
    """
    Build a deterministic ``solution_reveal`` trace.

    This is intentionally a presentation trace rather than an internal
    cover/uncover trace, so the format stays stable if the engine is optimized.
    """

    init_s = to_string(initial)
    sol_s = to_string(solved)
    steps: List[Dict[str, int]] = []
    for i, ch in enumerate(init_s):
        if ch == ".":
            r, c = divmod(i, 9)
            steps.append({"r": r, "c": c, "v": int(sol_s[i])})
    return {
        "version": "reveal-1",
        "kind": "solution_reveal",
        "initial": init_s,
        "solution": sol_s,
        "steps": steps,
        "stats": {
            "ms": int(round(stats.ms)),
            "nodes": int(stats.nodes),
            "backtracks": int(stats.backtracks),
        },
    }


def analyze(grid: Grid) -> Dict[str, Any]:
    """
    Return a compact analysis dictionary.

    Malformed (non-9x9 / out-of-range) grids are reported as invalid rather than
    raising from downstream canonicalization or rating code.
    """

    if not is_well_formed(grid):
        return {
            "version": ANALYZE_VERSION,
            "valid": False,
            "givens": 0,
            "solvable": False,
            "unique": False,
            "difficulty": 10.0,
            "canonical": "",
            "solution": None,
            "stats": {"ms": 0, "nodes": 0, "backtracks": 0},
        }

    from .canonical import canonical_form
    from .rating import rate

    givens = sum(1 for r in range(9) for c in range(9) if grid[r][c] != 0)
    valid = is_valid(grid)
    unique = False
    solved: Optional[SolveResult] = None
    if valid:
        unique = count_solutions(grid, limit=2) == 1
        solved = solve(grid)

    solution = None
    ms = nodes = backs = 0
    if solved is not None:
        solution = to_string(solved.grid)
        ms = int(round(solved.stats.ms))
        nodes = int(solved.stats.nodes)
        backs = int(solved.stats.backtracks)

    return {
        "version": ANALYZE_VERSION,
        "valid": valid,
        "givens": givens,
        "solvable": solved is not None,
        "unique": unique,
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
    "build_reveal_trace",
    "is_well_formed",
    "is_valid",
    "solve",
    "count_solutions",
    "analyze",
]
