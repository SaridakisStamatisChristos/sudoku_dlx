from concurrent.futures import ThreadPoolExecutor

import pytest

from sudoku_dlx import (
    canonical_form,
    count_solutions,
    from_string,
    generate,
    is_valid,
    solve,
    to_string,
)
from sudoku_dlx.solver import BitDLX, grid_clues, validate_grid


HARD_UNIQUE = "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
MULTI = ".....6....59.....82....8....45........3........6..3.54...325..6.................."


def _rot90(grid):
    return [[grid[8 - c][r] for c in range(9)] for r in range(9)]


def _assert_solution_extends(grid, solved):
    assert validate_grid(solved)
    assert all(value != 0 for row in solved for value in row)
    for r in range(9):
        for c in range(9):
            if grid[r][c]:
                assert solved[r][c] == grid[r][c]


def test_limit_two_retains_a_complete_first_solution_for_unique_puzzle():
    grid = from_string(HARD_UNIQUE)
    engine = BitDLX()
    count, solved = engine.count_solutions(grid_clues(grid), limit=2)

    assert count == 1
    assert solved is not None
    _assert_solution_extends(grid, solved)


def test_prepass_preserves_counts_and_valid_solutions():
    for text in (HARD_UNIQUE, MULTI):
        grid = from_string(text)
        clues = grid_clues(grid)

        fast = BitDLX()
        count_fast, solved_fast = fast.count_solutions(clues, limit=2, prepass=True)
        raw = BitDLX()
        count_raw, solved_raw = raw.count_solutions(clues, limit=2, prepass=False)

        assert count_fast == count_raw
        assert solved_fast is not None
        assert solved_raw is not None
        _assert_solution_extends(grid, solved_fast)
        _assert_solution_extends(grid, solved_raw)

        # A unique puzzle must yield the same solution. A multi-solution puzzle
        # may legitimately expose a different first solution after propagation.
        if count_fast == 1:
            assert to_string(solved_fast) == to_string(solved_raw)


def test_canonical_form_is_row_major_valid_and_idempotent():
    canonical = canonical_form(from_string(HARD_UNIQUE))
    parsed = from_string(canonical)

    assert len(canonical) == 81
    assert is_valid(parsed)
    assert canonical_form(parsed) == canonical


def test_canonical_form_is_invariant_under_d4_transform():
    grid = from_string(HARD_UNIQUE)
    assert canonical_form(_rot90(grid)) == canonical_form(grid)


def test_public_solver_is_reentrant_across_threads():
    def run_once():
        result = solve(from_string(HARD_UNIQUE))
        assert result is not None
        return (
            to_string(result.grid),
            result.stats.nodes,
            result.stats.branches,
            result.stats.backtracks,
            result.stats.max_depth,
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        outputs = list(pool.map(lambda _: run_once(), range(16)))

    assert len(set(outputs)) == 1


def test_public_validation_is_total_for_malformed_grids():
    assert not is_valid([])
    assert not is_valid([[0] * 9 for _ in range(8)])
    bad = [[0] * 9 for _ in range(9)]
    bad[0][0] = 10
    assert not is_valid(bad)
    assert solve(bad) is None
    assert count_solutions(bad) == 0


def test_solution_limit_is_validated():
    grid = from_string(HARD_UNIQUE)
    with pytest.raises(ValueError):
        count_solutions(grid, limit=0)
    with pytest.raises(ValueError):
        BitDLX().count_solutions(grid_clues(grid), limit=0)


def test_generator_is_seed_deterministic_and_validates_options():
    a = generate(seed=7331, target_givens=34, symmetry="mix")
    b = generate(seed=7331, target_givens=34, symmetry="mix")
    assert a == b
    assert count_solutions(a, limit=2) == 1

    with pytest.raises(ValueError):
        generate(seed=1, target_givens=16)
    with pytest.raises(ValueError):
        generate(seed=1, symmetry="diagonal")  # type: ignore[arg-type]


def test_rot180_mode_guarantees_final_clue_pattern_symmetry():
    puzzle = generate(seed=17, target_givens=34, symmetry="rot180")
    for r in range(9):
        for c in range(9):
            assert (puzzle[r][c] != 0) == (puzzle[8 - r][8 - c] != 0)
