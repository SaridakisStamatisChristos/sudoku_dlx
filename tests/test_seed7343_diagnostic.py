from __future__ import annotations

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
        before_candidates = [
            (r, c, sorted(state.candidates[r][c]))
            for r in range(9)
            for c in range(9)
            if state.grid[r][c] == 0
        ]

        try:
            move = state.step()
        except _LogicalContradiction as exc:
            after_missing = _missing_oracle_candidates(state, exact.grid)
            raise AssertionError(
                f"contradiction step={step_index} error={exc!s} missing={after_missing!r}"
            ) from exc

        if move is None:
            break

        after_missing = _missing_oracle_candidates(state, exact.grid)
        if after_missing:
            unit_kind = move.get("unit")
            unit_index = move.get("unit_index")
            relevant = []
            if unit_kind == "box":
                br, bc = (unit_index // 3) * 3, (unit_index % 3) * 3
                relevant = [
                    item
                    for item in before_candidates
                    if br <= item[0] < br + 3 and bc <= item[1] < bc + 3
                ]
            elif unit_kind == "row":
                relevant = [item for item in before_candidates if item[0] == unit_index]
            elif unit_kind == "col":
                relevant = [item for item in before_candidates if item[1] == unit_index]
            raise AssertionError(
                f"oracle violation step={step_index} move={move!r} "
                f"unit_before={relevant!r} missing={after_missing!r}"
            )

        if move["type"] == "place":
            assert move["v"] == exact.grid[move["r"]][move["c"]], (step_index, move)

    assert not state.contradiction
