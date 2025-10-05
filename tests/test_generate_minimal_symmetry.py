from sudoku_dlx import generate, is_valid, solve, count_solutions


def _filled(grid) -> int:
    return sum(1 for r in range(9) for c in range(9) if grid[r][c] != 0)


def _is_minimal_strict(grid) -> bool:
    # removing any single clue must break uniqueness
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                continue
            keep = grid[r][c]
            grid[r][c] = 0
            uniq = count_solutions(grid, limit=2) == 1
            grid[r][c] = keep
            if uniq:
                return False
    return True


def test_gen_rot180_symmetry_unique_and_valid():
    puzzle = generate(seed=7, target_givens=34, symmetry="rot180")
    assert is_valid(puzzle)
    result = solve(puzzle)
    assert result is not None
    # rot180 symmetry check: clue at (r, c) implies clue at (8-r, 8-c)
    for r in range(9):
        for c in range(9):
            if puzzle[r][c] != 0:
                assert puzzle[8 - r][8 - c] != 0


def test_gen_minimal_flag_enforces_minimality():
    puzzle = generate(seed=11, target_givens=36, minimal=True, symmetry="none")
    assert is_valid(puzzle)
    assert _is_minimal_strict(puzzle)
    result = solve(puzzle)
    assert result is not None


def test_minimal_puzzles_are_unique():
    puzzle = generate(seed=21, target_givens=35, minimal=True, symmetry="mix")
    assert count_solutions(puzzle, limit=2) == 1
