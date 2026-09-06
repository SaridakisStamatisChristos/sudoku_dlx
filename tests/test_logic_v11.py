import importlib

import pytest

from sudoku_dlx import (
    HUMAN_DIFFICULTY_VERSION,
    count_solutions,
    from_string,
    generate_result,
    human_rate,
    logical_solve,
    to_string,
)

EASY = (
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)

HARD = "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."

SOLVED = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"


def test_logical_solve_is_deterministic_and_does_not_mutate_input():
    grid = from_string(EASY)
    before = to_string(grid)

    first = logical_solve(grid)
    second = logical_solve(grid)

    assert to_string(grid) == before
    assert first.steps == second.steps
    assert first.grid == second.grid
    assert first.solved
    assert not first.contradiction
    assert to_string(first.grid) == SOLVED


def test_human_rate_has_separate_versioned_scale():
    easy = human_rate(from_string(EASY))
    solved = human_rate(from_string(SOLVED))

    assert HUMAN_DIFFICULTY_VERSION == "1"
    assert solved.score == 0.0
    assert solved.label == "easy"
    assert solved.solved_logically
    assert 0.0 <= easy.score <= 10.0
    assert easy.label in {"easy", "medium", "hard", "expert"}
    assert easy.steps > 0


def test_human_rate_is_deterministic_on_hard_unique_puzzle():
    grid = from_string(HARD)
    assert count_solutions(grid, limit=2) == 1

    first = human_rate(grid)
    second = human_rate(grid)

    assert first == second
    assert first.label in {"easy", "medium", "hard", "expert"}
    assert 0.0 <= first.score <= 10.0


def test_generation_result_is_reproducible_and_self_consistent():
    first = generate_result(seed=7331, target_givens=36, symmetry="mix")
    second = generate_result(seed=7331, target_givens=36, symmetry="mix")

    assert first.grid == second.grid
    assert first.solution == second.solution
    assert first.givens == second.givens
    assert first.machine_difficulty == second.machine_difficulty
    assert first.human_difficulty == second.human_difficulty
    assert first.attempts == 1
    assert count_solutions(first.grid, limit=2) == 1


def test_generate_rated_retry_logic_is_deterministic(monkeypatch):
    generate_module = importlib.import_module("sudoku_dlx.generate")
    calls = []

    def fake_result(seed=None, **kwargs):
        calls.append(seed)
        label = "medium" if len(calls) == 2 else "easy"
        rating = generate_module.HumanRating(
            version="1",
            score=4.0 if label == "medium" else 2.0,
            label=label,
            solved_logically=True,
            steps=10,
            placements=10,
            eliminations=0,
            hardest_strategy="hidden_single",
        )
        grid = from_string(SOLVED)
        return generate_module.GenerationResult(
            grid=grid,
            solution=grid,
            seed=seed,
            attempts=1,
            givens=81,
            symmetry="mix",
            minimality="none",
            machine_difficulty=0.0,
            human_difficulty=rating,
        )

    monkeypatch.setattr(generate_module, "generate_result", fake_result)

    result = generate_module.generate_rated("medium", seed=123, max_attempts=3)

    assert result.attempts == 2
    assert result.human_difficulty.label == "medium"
    assert len(calls) == 2


def test_generate_rated_validates_inputs():
    generate_module = importlib.import_module("sudoku_dlx.generate")
    with pytest.raises(ValueError):
        generate_module.generate_rated("impossible")
    with pytest.raises(ValueError):
        generate_module.generate_rated("easy", max_attempts=0)


def test_machine_rating_cache_is_bounded():
    rating_module = importlib.import_module("sudoku_dlx.rating")
    assert rating_module._rate_canonical.cache_parameters()["maxsize"] == 4096
