import math

from sudoku_dlx.solver import (
    BitDLX,
    SOLVER,
    deduce_singles_from_clues,
    from_string,
    generate_minimal,
    grid_clues,
    hardness_estimate,
    is_minimal,
    latin_base,
    permute_complete,
    print_grid,
    rot180_pairs,
    set_seed,
    to_string,
    validate_grid,
)


def test_dlx_search_handles_missing_column(monkeypatch):
    solver = BitDLX()
    monkeypatch.setattr(solver, "_choose_col", lambda rows_mask, cols_mask: None)
    result = solver._search(1, 1, limit=1, keep_one=False, collect_sol=[], found=[0])
    assert result is False


def test_dlx_search_handles_empty_candidates():
    solver = BitDLX()
    result = solver._search(0, 1, limit=1, keep_one=False, collect_sol=[], found=[0])
    assert result is False


def test_count_solutions_prepass_conflict():
    solver = BitDLX()
    cnt, grid = solver.count_solutions([(0, 0, 1), (0, 0, 2)])
    assert (cnt, grid) == (0, None)


def test_count_solutions_invalid_row():
    solver = BitDLX()
    cnt, grid = solver.count_solutions([(0, 0, 10)], prepass=False)
    assert (cnt, grid) == (0, None)


def test_count_solutions_no_solution_when_search_fails(monkeypatch):
    solver = BitDLX()

    def fake_search(rows_mask, cols_mask, limit, keep_one, collect_sol, found, depth=0):
        return False

    monkeypatch.setattr(solver, "_search", fake_search)
    cnt, grid = solver.count_solutions([(0, 0, 1)], prepass=False)
    assert (cnt, grid) == (0, None)


def test_iter_solutions_with_limit():
    puzzle = from_string(
        "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    )
    solutions = list(SOLVER.iter_solutions(grid_clues(puzzle), limit=1))
    assert len(solutions) == 1
    assert validate_grid(solutions[0])


def test_iter_solutions_invalid_prepass():
    solver = BitDLX()
    results = list(solver.iter_solutions([(0, 0, 1), (0, 0, 2)]))
    assert results == []


def test_iter_solutions_invalid_row():
    solver = BitDLX()
    results = list(solver.iter_solutions([(0, 0, 10)], prepass=False))
    assert results == []


def test_string_helpers_and_validation(capsys):
    grid = latin_base()
    text = to_string(grid)
    assert len(text) == 81
    roundtrip = from_string(text)
    assert roundtrip == grid
    assert validate_grid(grid)
    print_grid(grid)
    out = capsys.readouterr().out
    assert out.count("+-------") >= 4


def test_validate_grid_rejects_bad_values():
    grid = [[0] * 9 for _ in range(9)]
    grid[0][0] = 10
    assert validate_grid(grid) is False


def test_validate_grid_rejects_duplicates():
    grid = latin_base()
    grid[0][0] = grid[0][1]
    assert validate_grid(grid) is False


def test_deduce_singles_conflict():
    ok, extra = deduce_singles_from_clues([(0, 0, 1), (0, 0, 2)])
    assert ok is False
    assert extra == []


def test_deduce_singles_dead_end():
    clues = [(0, i, i + 1) for i in range(8)] + [(1, 8, 9)]
    ok, extra = deduce_singles_from_clues(clues)
    assert ok is False
    assert extra == []


def test_rot180_pairs_cover_board():
    pairs = rot180_pairs()
    assert len(pairs) == 41
    assert ((0, 0), (8, 8)) in pairs or ((8, 8), (0, 0)) in pairs


def test_generate_minimal_variants():
    set_seed(0)
    puzzle_mix, full_mix = generate_minimal(target_clues=24, symmetry="mix", seed=1)
    puzzle_rot, full_rot = generate_minimal(target_clues=24, symmetry="rot180", seed=2)
    puzzle_none, full_none = generate_minimal(target_clues=24, symmetry="none", seed=3)

    for puzzle, full in [(puzzle_mix, full_mix), (puzzle_rot, full_rot), (puzzle_none, full_none)]:
        assert validate_grid(full)
        cnt, _ = SOLVER.count_solutions(grid_clues(puzzle), limit=1)
        assert cnt == 1


def test_is_minimal_detects_non_minimal():
    grid = latin_base()
    puzzle = permute_complete(grid)
    puzzle[0][0] = 0
    puzzle[0][1] = 0
    assert is_minimal(puzzle) is False


def test_hardness_estimate_invalid_grid():
    grid = [[0] * 9 for _ in range(9)]
    grid[0][0] = 1
    grid[0][1] = 1
    assert math.isinf(hardness_estimate(grid))
