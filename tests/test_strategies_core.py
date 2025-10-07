from __future__ import annotations

from unittest.mock import patch

from sudoku_dlx.strategies import (
    apply_box_line_claiming,
    apply_hidden_pair,
    apply_hidden_single,
    apply_hidden_triple,
    apply_hidden_single,
    apply_locked_candidates_pointing,
    apply_naked_single,
    apply_naked_pair,
    apply_naked_triple,
    apply_x_wing,
    candidates,
    step_once,
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


def test_naked_single_places_value() -> None:
    grid = _empty_grid()
    for c, value in enumerate(range(1, 9)):
        grid[0][c] = value
    cand = candidates(grid)

    move = apply_naked_single(grid, cand)

    assert move is not None
    assert move["strategy"] == "naked_single"
    assert move["type"] == "place"
    assert move["r"] == 0 and move["c"] == 8
    assert move["v"] == 9
    assert grid[0][8] == 9


def test_hidden_single_row_metadata() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digit = 7
    _clear_digit(cand, digit)
    cand[2][4].update({digit, 9})

    move = apply_hidden_single(grid, cand)

    assert move is not None
    assert move["strategy"] == "hidden_single"
    assert move["unit"] == "row"
    assert move["unit_index"] == 2
    assert move["r"] == 2 and move["c"] == 4
    assert move["v"] == digit
    assert grid[2][4] == digit


def test_hidden_single_column_metadata() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digit = 5
    _clear_digit(cand, digit)
    cand[1][3].update({digit, 9})
    cand[1][5].add(digit)

    move = apply_hidden_single(grid, cand)

    assert move is not None
    assert move["strategy"] == "hidden_single"
    assert move["unit"] == "col"
    assert move["unit_index"] == 3
    assert move["r"] == 1 and move["c"] == 3
    assert move["v"] == digit
    assert grid[1][3] == digit


def test_hidden_single_box_metadata() -> None:
    grid = _empty_grid()
    cand = candidates(grid)
    digit = 6
    _clear_digit(cand, digit)
    for r, c in (
        (7, 7),
        (7, 0),
        (4, 7),
        (4, 6),
        (1, 6),
        (1, 2),
        (5, 2),
        (5, 5),
        (0, 5),
        (0, 3),
        (6, 3),
        (6, 4),
        (3, 4),
        (3, 0),
        (2, 0),
        (2, 1),
        (1, 1),
        (2, 7),
        (6, 1),
    ):
        cand[r][c].add(digit)

    move = apply_hidden_single(grid, cand)

    assert move is not None
    assert move["strategy"] == "hidden_single"
    assert move["unit"] == "box"
    assert move["unit_index"] == 8
    assert move["r"] == 7 and move["c"] == 7
    assert move["v"] == digit
    assert grid[7][7] == digit


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


def test_step_once_prefers_naked_single_over_hidden_single() -> None:
    grid = _empty_grid()
    cand = candidates(grid)

    _set_candidates(cand, 0, 0, {1})
    _set_candidates(cand, 0, 1, {2, 3})
    for c in range(9):
        if c != 1:
            cand[0][c].discard(2)

    grid_hidden = [row[:] for row in grid]
    cand_hidden = [[cell.copy() for cell in row] for row in cand]
    hidden_move = apply_hidden_single(grid_hidden, cand_hidden)

    assert hidden_move is not None
    assert hidden_move["strategy"] == "hidden_single"

    with patch("sudoku_dlx.strategies.candidates", return_value=cand):
        move = step_once(grid)

    assert move is not None
    assert move["strategy"] == "naked_single"
    assert move["r"] == 0 and move["c"] == 0
    assert grid[0][0] == 1


def test_step_once_prioritizes_locked_pointing_before_box_line() -> None:
    grid = _empty_grid()
    cand = candidates(grid)

    for r in range(3):
        for c in range(3):
            cand[r][c].discard(1)
    _set_candidates(cand, 0, 0, {1, 2})
    _set_candidates(cand, 0, 1, {1, 3})
    _set_candidates(cand, 0, 5, {1, 4, 5})

    for c in range(9):
        if c not in (3, 4):
            cand[1][c].discard(4)
    _set_candidates(cand, 1, 3, {4, 5})
    _set_candidates(cand, 1, 4, {4, 6})
    _set_candidates(cand, 0, 3, {2, 4, 7})

    grid_locked = [row[:] for row in grid]
    cand_locked = [[cell.copy() for cell in row] for row in cand]
    locked_move = apply_locked_candidates_pointing(grid_locked, cand_locked)

    assert locked_move is not None
    assert locked_move["strategy"].startswith("locked_pointing")

    grid_box_line = [row[:] for row in grid]
    cand_box_line = [[cell.copy() for cell in row] for row in cand]
    box_line_move = apply_box_line_claiming(grid_box_line, cand_box_line)

    assert box_line_move is not None
    assert box_line_move["strategy"].startswith("box_line")

    with patch("sudoku_dlx.strategies.candidates", return_value=cand):
        move = step_once(grid)

    assert move is not None
    assert move["strategy"].startswith("locked_pointing")
    assert grid == _empty_grid()


def test_step_once_returns_none_when_no_moves_available() -> None:
    grid = _empty_grid()
    snapshot = [row[:] for row in grid]

    move = step_once(grid)

    assert move is None
    assert grid == snapshot
