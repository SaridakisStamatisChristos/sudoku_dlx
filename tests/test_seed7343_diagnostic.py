from __future__ import annotations

import pytest

from sudoku_dlx import generate, solve
from sudoku_dlx.logic import LogicalState, _LogicalContradiction


def _missing_oracle_candidates(state: LogicalState, exact_grid: list[list[int]]):
    return [
        (r, c, exact_grid[r][c], sorted(state.candidates[r][c]))
        for r in range(9)
        for c in range(9)
        if state.grid[r][c] == 0 and exact_grid[r][c] not in state.candidates[r][c]
    ]


def test_seed_7343_first_oracle_violation_is_localized():
    grid = generate(seed=7343, target_givens=30, symmetry="mix")
    exact = solve(grid, collect_stats=False)
    assert exact is not None

    state = LogicalState(grid)
    assert not _missing_oracle_candidates(state, exact.grid)

    for step_index in range(500):
        before_missing = _missing_oracle_candidates(state, exact.grid)
        assert not before_missing, ("before", step_index, state.steps[-5:], before_missing)

        try:
            move = state.step()
        except _LogicalContradiction as exc:
            after_missing = _missing_oracle_candidates(state, exact.grid)
            raise AssertionError(
                (
                    "contradiction",
                    step_index,
                    str(exc),
                    state.hardest_strategy,
                    state.steps[-5:],
                    after_missing,
                )
            ) from exc

        if move is None:
            break

        after_missing = _missing_oracle_candidates(state, exact.grid)
        assert not after_missing, ("after", step_index, move, state.steps[-5:], after_missing)

        if move["type"] == "place":
            assert move["v"] == exact.grid[move["r"]][move["c"]], (step_index, move)

    assert not state.contradiction
