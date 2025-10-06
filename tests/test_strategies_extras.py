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
