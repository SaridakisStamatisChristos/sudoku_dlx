from __future__ import annotations

from sudoku_dlx.strategies import (
    apply_box_line_claiming,
    apply_hidden_pair,
    apply_hidden_triple,
    apply_locked_candidates_pointing,
    apply_naked_pair,
    apply_naked_triple,
    apply_x_wing,
    candidates,
)


def _empty_grid() -> list[list[int]]:
    return [[0] * 9 for _ in range(9)]


def _clear_digit(cand: list[list[set[int]]], digit: int) -> None:
    for row in cand:
        for cell in row:
            cell.discard(digit)


def _set_candidates(cand: list[list[set[int]]], r: int, c: int, values: set[int]) -> None:
    cand[r][c].clear()
    cand[r][c].update(values)


def test_locked_candidates_pointing_row() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digit = 7
    _clear_digit(cand, digit)
    for c in range(3):
        cand[0][c].add(digit)
    cand[0][4].add(digit)

    move = apply_locked_candidates_pointing(grid, cand)

    assert move is not None
    assert move["strategy"] == "locked_pointing_row"
    assert move["r"] == 0 and move["c"] == 4
    assert digit not in cand[0][4]


def test_locked_candidates_pointing_col() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digit = 5
    _clear_digit(cand, digit)
    for r in range(3):
        cand[r][1].add(digit)
    cand[4][1].add(digit)

    move = apply_locked_candidates_pointing(grid, cand)

    assert move is not None
    assert move["strategy"] == "locked_pointing_col"
    assert move["c"] == 1 and move["r"] == 4
    assert digit not in cand[4][1]


def test_box_line_claiming_row() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digit = 6
    _clear_digit(cand, digit)
    for c in range(3):
        cand[0][c].add(digit)
    cand[1][0].add(digit)

    move = apply_box_line_claiming(grid, cand)

    assert move is not None
    assert move["strategy"] == "box_line_row"
    assert move["box"] == 0
    assert digit not in cand[1][0]


def test_box_line_claiming_col() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digit = 4
    _clear_digit(cand, digit)
    cand[0][0].add(digit)
    cand[1][0].add(digit)
    cand[2][1].add(digit)

    move = apply_box_line_claiming(grid, cand)

    assert move is not None
    assert move["strategy"] == "box_line_col"
    assert move["box"] == 0
    assert move["r"] == 2 and move["c"] == 1
    assert digit not in cand[2][1]


def test_naked_pair_eliminates_other_candidates() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    _clear_digit(cand, 1)
    _clear_digit(cand, 2)
    _clear_digit(cand, 3)
    _set_candidates(cand, 0, 0, {1, 2})
    _set_candidates(cand, 0, 1, {1, 2})
    _set_candidates(cand, 0, 2, {1, 2, 3})

    move = apply_naked_pair(grid, cand)

    assert move is not None
    assert move["strategy"] == "naked_pair"
    assert move["r"] == 0 and move["c"] == 2
    assert move["pair"] == [1, 2]
    assert move["remove"] in (1, 2)
    assert move["remove"] not in cand[0][2]


def test_hidden_pair_prunes_extras() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digit_a, digit_b, extra = 7, 8, 9
    _clear_digit(cand, digit_a)
    _clear_digit(cand, digit_b)
    _clear_digit(cand, extra)
    _set_candidates(cand, 1, 0, {digit_a, digit_b, extra})
    _set_candidates(cand, 1, 1, {digit_a, digit_b, extra})

    move = apply_hidden_pair(grid, cand)

    assert move is not None
    assert move["strategy"] == "hidden_pair"
    assert move["r"] in (1,)
    assert move["c"] in (0, 1)
    assert move["remove"] == extra
    first_target = (move["r"], move["c"])
    assert cand[first_target[0]][first_target[1]] == {digit_a, digit_b}

    move_second = apply_hidden_pair(grid, cand)

    assert move_second is not None
    assert move_second["strategy"] == "hidden_pair"
    assert (move_second["r"], move_second["c"]) != first_target
    assert move_second["remove"] == extra
    second_target = (move_second["r"], move_second["c"])
    assert cand[second_target[0]][second_target[1]] == {digit_a, digit_b}


def test_naked_triple_clears_unit() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digits = (1, 2, 3, 4)
    for d in digits:
        _clear_digit(cand, d)
    _set_candidates(cand, 2, 0, {1, 2})
    _set_candidates(cand, 2, 1, {1, 3})
    _set_candidates(cand, 2, 2, {2, 3})
    _set_candidates(cand, 2, 3, {1, 4})

    before = {pos: cand[pos[0]][pos[1]].copy() for pos in ((2, 0), (2, 1), (2, 2), (2, 3))}

    move = apply_naked_triple(grid, cand)

    assert move is not None
    assert move["strategy"] == "naked_triple"
    assert move["unit"] == "row"
    assert move["unit_index"] == 2
    target = (move["r"], move["c"])
    removed = move["v"]

    assert target[0] == 2
    assert target in before
    assert removed in {1, 2, 3}
    assert removed in before[target]
    assert cand[target[0]][target[1]] == before[target] - {removed}


def test_hidden_triple_culls_extras() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    triple = (4, 5, 6)
    extra = 7
    for d in (*triple, extra):
        _clear_digit(cand, d)
    _set_candidates(cand, 3, 0, {4, 5, extra})
    _set_candidates(cand, 3, 1, {4, 6})
    _set_candidates(cand, 3, 2, {5, 6})

    move = apply_hidden_triple(grid, cand)

    assert move is not None
    assert move["strategy"] == "hidden_triple"
    assert move["r"] == 3 and move["c"] == 0
    assert extra not in cand[3][0]


def test_x_wing_rows_then_cols() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digit_row = 9
    _clear_digit(cand, digit_row)
    for c in (2, 6):
        cand[1][c].add(digit_row)
        cand[5][c].add(digit_row)
    cand[0][2].add(digit_row)

    move_row = apply_x_wing(grid, cand)

    assert move_row is not None
    assert move_row["strategy"] == "x_wing_row"
    assert move_row["digit"] == digit_row
    assert digit_row not in cand[0][2]

    grid2 = _empty_grid()
    cand2 = candidates(grid2)
    digit_col = 4
    _clear_digit(cand2, digit_col)
    for r in (3, 6):
        cand2[r][1].add(digit_col)
        cand2[r][7].add(digit_col)
    cand2[3][0].add(digit_col)

    move_col = apply_x_wing(grid2, cand2)

    assert move_col is not None
    assert move_col["strategy"] == "x_wing_col"
    assert move_col["digit"] == digit_col
    assert digit_col not in cand2[3][0]
