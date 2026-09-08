from __future__ import annotations

from sudoku_dlx import generate, solve
from sudoku_dlx.logic import LogicalState


def _missing_oracle_candidates(state: LogicalState, exact_grid: list[list[int]]):
    return [
        (r, c, exact_grid[r][c], sorted(state.candidates[r][c]))
        for r in range(9)
        for c in range(9)
        if state.grid[r][c] == 0 and exact_grid[r][c] not in state.candidates[r][c]
    ]


def test_seed_7343_human_logic_preserves_exact_solution_oracle():
    """Regression for the naked-triple source-cell corruption found on seed 7343."""

    grid = generate(seed=7343, target_givens=30, symmetry="mix")
    exact = solve(grid, collect_stats=False)
    assert exact is not None

    state = LogicalState(grid)
    assert not _missing_oracle_candidates(state, exact.grid)

    for step_index in range(500):
        move = state.step()
        if move is None:
            break

        missing = _missing_oracle_candidates(state, exact.grid)
        assert not missing, (step_index, move, missing)

        if move["type"] == "place":
            assert move["v"] == exact.grid[move["r"]][move["c"]], (step_index, move)

    assert not state.contradiction
