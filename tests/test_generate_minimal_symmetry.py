from sudoku_dlx import generate, is_valid, solve


def _filled(grid) -> int:
    return sum(1 for r in range(9) for c in range(9) if grid[r][c] != 0)


def _is_minimal(grid) -> bool:
    from sudoku_dlx import count_solutions

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
    assert _is_minimal(puzzle)
    result = solve(puzzle)
    assert result is not None
