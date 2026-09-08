from __future__ import annotations

from sudoku_dlx.strategies import apply_naked_triple, candidates


def _empty_grid() -> list[list[int]]:
    return [[0] * 9 for _ in range(9)]


def test_naked_triple_never_eliminates_from_its_source_cells() -> None:
    grid = _empty_grid()
    cand = candidates(grid)

    # Three legitimate naked-triple source cells in row 0.
    cand[0][0] = {1, 2}
    cand[0][1] = {1, 3}
    cand[0][2] = {2, 3}
    # Keep the first outside target out of the source-cell search (size 4).
    cand[0][3] = {1, 2, 3, 4}

    source_before = [set(cand[0][c]) for c in range(3)]
    move = apply_naked_triple(grid, cand)

    assert move is not None
    assert move["strategy"] == "naked_triple"
    assert (move["r"], move["c"]) == (0, 3)
    assert [cand[0][c] for c in range(3)] == source_before
    assert cand[0][3] == {2, 3, 4}


def test_naked_triple_requires_exactly_three_distinct_digits() -> None:
    grid = _empty_grid()
    cand = candidates(grid)

    # Three cells restricted to only two distinct digits are not a naked triple.
    cand[0][0] = {1, 2}
    cand[0][1] = {1, 2}
    cand[0][2] = {1, 2}
    cand[0][3] = {1, 2, 3, 4}

    before = [set(cell) for cell in cand[0]]
    move = apply_naked_triple(grid, cand)

    assert move is None
    assert cand[0] == before
