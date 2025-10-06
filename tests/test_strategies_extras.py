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
    for r in range(2):
        for c in range(9):
            cand[r][c].discard(digit)
        cand[r][0].add(digit)
        cand[r][3].add(digit)
    cand[2][0].add(digit)

    move = apply_simple_coloring(grid, cand)
    assert move is not None
    assert move["strategy"] == "simple_coloring"
    assert digit not in cand[move["r"]][move["c"]]
