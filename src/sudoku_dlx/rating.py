from __future__ import annotations

import math

from .api import Grid, from_string, is_valid, solve
from .canonical import canonical_form

DIFFICULTY_VERSION = "3"

_RATING_CACHE: dict[str, float] = {}


def rate(grid: Grid) -> float:
    """
    Return deterministic heuristic difficulty in ``[0, 10]``.

    v3 deliberately rates the canonical representative rather than the caller's
    particular row/column/digit labeling. This makes the score invariant under
    the same Sudoku isomorphisms used by ``canonical_form`` without relying on
    cache insertion order.

    Features are machine-independent search-work counters:
      - clue sparsity
      - log-scaled exact-cover nodes
      - log-scaled failed branches (backtracks)
      - failed-branch ratio

    Invalid or unsatisfiable puzzles rate as 10.0.
    """

    if not is_valid(grid):
        return 10.0

    signature = canonical_form(grid)
    cached = _RATING_CACHE.get(signature)
    if cached is not None:
        return cached

    canonical_grid = from_string(signature)
    result = solve(canonical_grid)
    if result is None:
        return 10.0

    givens = sum(1 for row in canonical_grid for value in row if value != 0)
    empties = 81 - givens
    stats = result.stats

    def log01(value: int, scale: int) -> float:
        return min(math.log1p(max(0, value)) / math.log1p(scale), 1.0)

    sparsity = min(empties / 64.0, 1.0)
    node_work = log01(stats.nodes, 50_000)
    backtrack_work = log01(stats.backtracks, 5_000)
    failure_ratio = min(stats.backtracks / max(1, stats.branches), 1.0)

    score01 = (
        0.20 * sparsity
        + 0.45 * node_work
        + 0.25 * backtrack_work
        + 0.10 * failure_ratio
    )
    score = round(10.0 * min(max(score01, 0.0), 1.0), 1)
    _RATING_CACHE[signature] = score
    return score


__all__ = ["DIFFICULTY_VERSION", "rate"]
