from __future__ import annotations

from .api import Grid, solve


def rate(grid: Grid) -> float:
    """Estimate puzzle difficulty in [0, 10]."""
    givens = sum(1 for r in range(9) for c in range(9) if grid[r][c] != 0)
    result = solve([row[:] for row in grid])
    if result is None:
        return 10.0
    features = (
        (81 - givens) / 60.0,
        min(result.stats.nodes / 50000.0, 1.5),
        min(result.stats.backtracks / 5000.0, 1.5),
    )
    score = 10.0 * min(features[0] * 0.5 + features[1] * 0.35 + features[2] * 0.15, 1.0)
    return round(score, 1)


__all__ = ["rate"]
