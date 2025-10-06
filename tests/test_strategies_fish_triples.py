from sudoku_dlx.strategies import (
    candidates,
    apply_naked_triple,
    apply_hidden_triple,
    apply_x_wing,
)


def test_naked_triple_eliminates_one_in_row():
    g = [[0] * 9 for _ in range(9)]
    cand = candidates(g)
    cand[0][0] = {1, 2}
    cand[0][1] = {2, 3}
    cand[0][2] = {1, 3}
    cand[0][5].update({1, 4, 7})
    mv = apply_naked_triple(g, cand)
    assert mv is not None and mv["strategy"] == "naked_triple"
    r, c, v = mv["r"], mv["c"], mv["v"]
    assert v not in cand[r][c]


def test_hidden_triple_eliminates_extra_in_box():
    g = [[0] * 9 for _ in range(9)]
    cand = candidates(g)
    cand[0][0] = {4, 5, 7}
    cand[1][1] = {4, 6}
    cand[2][2] = {5, 6}
    for r in range(0, 3):
        for c in range(0, 3):
            if (r, c) not in [(0, 0), (1, 1), (2, 2)]:
                cand[r][c] = {1, 2, 3, 7, 8, 9} - {4, 5, 6}
    mv = apply_hidden_triple(g, cand)
    assert mv is not None and mv["strategy"] == "hidden_triple"
    assert mv["remove"] not in set(mv["triple"])


def test_x_wing_row_eliminates_in_other_rows():
    g = [[0] * 9 for _ in range(9)]
    cand = candidates(g)
    d = 7
    rows = [1, 4]
    cols = [2, 6]
    for r in rows:
        for c in range(9):
            cand[r][c].discard(d)
        cand[r][cols[0]].add(d)
        cand[r][cols[1]].add(d)
    cand[0][cols[0]].add(d)
    mv = apply_x_wing(g, cand)
    assert mv is not None and mv["strategy"] in ("x_wing_row", "x_wing_col")
    assert d not in cand[mv["r"]][mv["c"]]
