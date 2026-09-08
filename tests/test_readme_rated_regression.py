from sudoku_dlx import count_solutions, generate_rated


def test_readme_medium_rated_generation_seed_7331():
    result = generate_rated(
        "medium",
        seed=7331,
        symmetry="mix",
        max_attempts=64,
    )
    assert result.human_difficulty.label == "medium"
    assert count_solutions(result.grid, limit=2) == 1
