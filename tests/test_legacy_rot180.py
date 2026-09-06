from sudoku_dlx.solver import BitDLX, generate_minimal, grid_clues, is_minimal, rot180_pairs


def _is_rot180_pattern(puzzle):
    return all(
        (puzzle[r][c] != 0) == (puzzle[8 - r][8 - c] != 0)
        for r in range(9)
        for c in range(9)
    )


def _is_rot180_orbit_minimal(puzzle):
    solver = BitDLX()
    assert solver.count_solutions(grid_clues(puzzle), limit=2)[0] == 1

    for (r1, c1), (r2, c2) in rot180_pairs():
        candidate = [row[:] for row in puzzle]
        candidate[r1][c1] = 0
        candidate[r2][c2] = 0
        if candidate == puzzle:
            continue
        if solver.count_solutions(grid_clues(candidate), limit=2)[0] == 1:
            return False
    return True


def test_legacy_rot180_preserves_symmetry_and_orbit_minimality():
    for seed in (2, 17, 7331):
        puzzle, full = generate_minimal(target_clues=34, symmetry="rot180", seed=seed)
        assert _is_rot180_pattern(puzzle)
        assert _is_rot180_orbit_minimal(puzzle)
        assert all(value != 0 for row in full for value in row)


def test_legacy_none_and_mix_remain_strictly_minimal():
    puzzle_none, _ = generate_minimal(target_clues=30, symmetry="none", seed=3)
    puzzle_mix, _ = generate_minimal(target_clues=30, symmetry="mix", seed=1)

    assert is_minimal(puzzle_none)
    assert is_minimal(puzzle_mix)
