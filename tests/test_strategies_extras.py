from sudoku_dlx.strategies import candidates, apply_swordfish, apply_simple_coloring


def test_swordfish_synthetic_single_elimination() -> None:
    grid = [[0] * 9 for _ in range(9)]
    cand = candidates(grid)
    digit = 5
    rows = [1, 4, 7]
    cols = [2, 5, 8]
    for r in rows:
        for c in range(9):
            cand[r][c].discard(digit)
        for c in cols:
            cand[r][c].add(digit)
    cand[0][2].add(digit)

    move = apply_swordfish(grid, cand)
    assert move is not None
    assert move["strategy"].startswith("swordfish")
    assert digit not in cand[move["r"]][move["c"]]


def test_swordfish_col_eliminates_extra_row_candidate() -> None:
    grid = [[0] * 9 for _ in range(9)]
    cand = candidates(grid)
    digit = 7
    rows = [0, 4, 8]
    cols = [1, 4, 7]

    for r in range(9):
        for c in range(9):
            cand[r][c].discard(digit)

    for c in cols:
        for r in rows:
            cand[r][c].add(digit)

    target_row = rows[0]
    target_col = 0
    cand[target_row][target_col].add(digit)

    move = apply_swordfish(grid, cand)

    assert move is not None
    assert move["strategy"] == "swordfish_col"
    assert move["digit"] == digit
    assert (move["r"], move["c"]) == (target_row, target_col)
    assert digit not in cand[target_row][target_col]


def test_simple_coloring_one_elimination() -> None:
    grid = [[0] * 9 for _ in range(9)]
    cand = candidates(grid)
    digit = 9
    # Limit digit to four cells in box 0 forming a 2x2 square. Rows and columns
    # now contain conjugate links for the digit, so simple coloring Rule 2
    # should identify a conflict inside the box and eliminate one candidate.
    for r in range(9):
        for c in range(9):
            cand[r][c].discard(digit)
    for r, c in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        cand[r][c].add(digit)

    move = apply_simple_coloring(grid, cand)
    assert move is not None
    assert move["strategy"] == "simple_coloring"
    assert move["digit"] == digit
    assert digit not in cand[move["r"]][move["c"]]


def test_simple_coloring_reports_row_conflict_metadata() -> None:
    grid = [[0] * 9 for _ in range(9)]
    cand = candidates(grid)
    digit = 4

    for r in range(9):
        for c in range(9):
            cand[r][c].discard(digit)

    # Build a coloring component where two same-colored nodes share row 1.
    # Row 1 contains three candidates so no conjugate link is created there.
    pattern = [(1, 1), (4, 1), (4, 7), (2, 7), (1, 8), (1, 4)]
    for r, c in pattern:
        cand[r][c].add(digit)

    move = apply_simple_coloring(grid, cand)
    assert move is not None
    assert move["strategy"] == "simple_coloring"
    assert move["digit"] == digit
    assert move["unit"] == "row"
    assert move["unit_index"] == 1
    assert (move["r"], move["c"]) == (1, 1)
    assert digit not in cand[1][1]


def test_simple_coloring_reports_column_conflict_metadata() -> None:
    grid = [[0] * 9 for _ in range(9)]
    cand = candidates(grid)
    digit = 6

    for r in range(9):
        for c in range(9):
            cand[r][c].discard(digit)

    # Analogous setup forcing two same-colored nodes to appear in column 1.
    pattern = [(1, 1), (1, 4), (7, 4), (7, 2), (8, 1), (4, 1)]
    for r, c in pattern:
        cand[r][c].add(digit)

    move = apply_simple_coloring(grid, cand)
    assert move is not None
    assert move["strategy"] == "simple_coloring"
    assert move["digit"] == digit
    assert move["unit"] == "col"
    assert move["unit_index"] == 1
    assert (move["r"], move["c"]) == (1, 1)
    assert digit not in cand[1][1]
