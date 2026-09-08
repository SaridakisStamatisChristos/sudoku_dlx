from __future__ import annotations

import sys

import pytest

from sudoku_dlx import generate, logical_solve, solve


@pytest.mark.skipif(
    sys.version_info[:2] != (3, 12),
    reason="one-lane repair validation; nightly property workflow retains the permanent full sweep",
)
def test_repair_full_human_logic_oracle_sweep() -> None:
    """Temporarily run the nightly 60-puzzle oracle sweep in the PR gate."""

    for givens in (34, 30, 26):
        for seed in range(7331, 7351):
            grid = generate(seed=seed, target_givens=givens, symmetry="mix")
            exact = solve(grid, collect_stats=False)
            assert exact is not None

            logical = logical_solve(grid)
            assert not logical.contradiction, (givens, seed, logical.hardest_strategy)

            for step in logical.steps:
                r, c = step["r"], step["c"]
                if step["type"] == "place":
                    assert step["v"] == exact.grid[r][c], (givens, seed, step)
                else:
                    removed = step.get("remove", step.get("v", step.get("digit")))
                    assert removed != exact.grid[r][c], (givens, seed, step)
