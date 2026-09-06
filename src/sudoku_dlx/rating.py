from __future__ import annotations

from functools import lru_cache
import math

from .api import Grid, from_string, is_valid, solve
from .canonical import canonical_form

DIFFICULTY_VERSION = "3"


@lru_cache(maxsize=4096)
def _rate_canonical(signature: str) -> float:
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
    return round(10.0 * min(max(score01, 0.0), 1.0), 1)


def rate_canonical(signature: str) -> float:
    """Rate an already-canonical row-major puzzle string using Difficulty v3."""

    return _rate_canonical(signature)


def rate(grid: Grid) -> float:
    """
    Return deterministic heuristic difficulty in ``[0, 10]``.

    v3 rates the canonical representative using machine-independent exact-cover
    search work. The canonical-score cache is bounded in v1.1.
    """

    if not is_valid(grid):
        return 10.0
    return rate_canonical(canonical_form(grid))


__all__ = ["DIFFICULTY_VERSION", "rate"]
