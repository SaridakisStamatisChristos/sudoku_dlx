import pytest

from sudoku_dlx import generate, logical_solve, solve


@pytest.mark.prop
def test_generated_human_moves_preserve_exact_solution_oracle():
    """No deterministic human move may contradict the unique DLX solution."""

    for givens in (34, 30, 26):
        for seed in range(7331, 7351):
            grid = generate(seed=seed, target_givens=givens, symmetry="mix")
            exact = solve(grid, collect_stats=False)
            assert exact is not None

            logical = logical_solve(grid)
            assert not logical.contradiction, (givens, seed, logical.hardest_strategy)

            for step in logical.steps:
                r = step["r"]
                c = step["c"]
                if step["type"] == "place":
                    assert step["v"] == exact.grid[r][c], (givens, seed, step)
                    continue

                removed = step.get("remove")
                if removed is None:
                    removed = step.get("v")
                if removed is None:
                    removed = step.get("digit")
                assert removed is not None, (givens, seed, step)
                assert removed != exact.grid[r][c], (givens, seed, step)
