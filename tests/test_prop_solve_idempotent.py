from sudoku_dlx import generate, solve


def _is_full_valid(grid):
    # rows/cols/boxes each contain digits 1..9
    rows = [{grid[r][c] for c in range(9)} for r in range(9)]
    cols = [{grid[r][c] for r in range(9)} for c in range(9)]
    boxes = [
        {grid[r + i][c + j] for i in range(3) for j in range(3)}
        for r in (0, 3, 6)
        for c in (0, 3, 6)
    ]
    expect = set(range(1, 10))
    return all(s == expect for s in rows + cols + boxes)


def test_solve_idempotent_and_valid_small_seedset():
    # keep seeds small for CI speed
    for seed in [1, 3, 7]:
        p = generate(seed=seed, target_givens=34, minimal=False, symmetry="none")
        res1 = solve([row[:] for row in p])
        assert res1 is not None
        assert _is_full_valid(res1.grid)
        # solving a solved grid should be a no-op
        res2 = solve([row[:] for row in res1.grid])
        assert res2 is not None
        assert res2.grid == res1.grid
