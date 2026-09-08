import importlib

import pytest


def test_logical_run_surfaces_strategy_contradiction_without_raising(monkeypatch):
    logic = importlib.import_module("sudoku_dlx.logic")
    state = logic.LogicalState([[0] * 9 for _ in range(9)])
    state.candidates[0][0] = {1}

    def bad_elimination(_grid, candidates):
        candidates[0][0].remove(1)
        return {
            "type": "eliminate",
            "strategy": "bad_test_elimination",
            "r": 0,
            "c": 0,
            "remove": 1,
        }

    monkeypatch.setattr(logic, "_PLACEMENT_STRATEGIES", ())
    monkeypatch.setattr(logic, "_ELIMINATION_STRATEGIES", (bad_elimination,))

    result = state.run(max_steps=1)

    assert result.contradiction
    assert not result.solved
    assert not result.stalled
    assert not result.limit_reached


def test_candidate_contradiction_detects_missing_unit_support():
    logic = importlib.import_module("sudoku_dlx.logic")
    state = logic.LogicalState([[0] * 9 for _ in range(9)])

    for c in range(9):
        state.candidates[0][c].discard(9)

    assert all(state.candidates[0][c] for c in range(9))
    assert state._has_contradiction()


def test_human_rate_preserves_contradiction_diagnostic(monkeypatch):
    logic = importlib.import_module("sudoku_dlx.logic")

    monkeypatch.setattr(
        logic,
        "logical_solve",
        lambda _grid, max_steps=500: logic.LogicalResult(
            grid=[[0] * 9 for _ in range(9)],
            steps=[],
            solved=False,
            stalled=False,
            contradiction=True,
            limit_reached=False,
            hardest_strategy="hidden_pair",
        ),
    )

    rating = logic.human_rate([[0] * 9 for _ in range(9)])

    assert rating.label == "expert"
    assert not rating.solved_logically
    assert rating.contradiction


@pytest.mark.parametrize(
    ("strategy", "minimum_score", "expected_label"),
    [
        ("x_wing_row", 6.0, "hard"),
        ("x_wing_col", 6.0, "hard"),
        ("swordfish_row", 7.5, "expert"),
        ("swordfish_col", 7.5, "expert"),
    ],
)
def test_fish_strategy_names_receive_their_difficulty_weights(
    monkeypatch, strategy, minimum_score, expected_label
):
    logic = importlib.import_module("sudoku_dlx.logic")
    solved = [[((r * 3 + r // 3 + c) % 9) + 1 for c in range(9)] for r in range(9)]

    monkeypatch.setattr(
        logic,
        "logical_solve",
        lambda _grid, max_steps=500: logic.LogicalResult(
            grid=[row[:] for row in solved],
            steps=[{"type": "eliminate", "strategy": strategy}],
            solved=True,
            stalled=False,
            contradiction=False,
            limit_reached=False,
            hardest_strategy=strategy,
        ),
    )

    rating = logic.human_rate([[0] * 9 for _ in range(9)])

    assert rating.score >= minimum_score
    assert rating.label == expected_label
    assert not rating.contradiction
