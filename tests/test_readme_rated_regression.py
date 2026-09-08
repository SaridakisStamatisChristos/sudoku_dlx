import pytest

from sudoku_dlx import count_solutions, generate_rated


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard", "expert"])
def test_rated_generation_seed_7331_is_reproducible_and_usable(difficulty):
    first = generate_rated(
        difficulty,
        seed=7331,
        symmetry="mix",
        max_attempts=64,
    )
    second = generate_rated(
        difficulty,
        seed=7331,
        symmetry="mix",
        max_attempts=64,
    )

    assert first == second
    assert first.human_difficulty.label == difficulty
    assert not first.human_difficulty.contradiction
    assert count_solutions(first.grid, limit=2) == 1
