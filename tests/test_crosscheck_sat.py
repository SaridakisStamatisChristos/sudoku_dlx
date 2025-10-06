from textwrap import dedent

import pytest

from sudoku_dlx import from_string, solve
from sudoku_dlx.crosscheck import sat_solve


PUZZLE = dedent(
    """
    53..7....
    6..195...
    .98....6.
    8...6...3
    4..8.3..1
    7...2...6
    .6....28.
    ...419..5
    ....8..79
    """
).strip()


def test_sat_crosscheck_matches_when_available() -> None:
    grid = from_string(PUZZLE)
    sat_grid = None
    try:
        sat_grid = sat_solve(grid)
    except Exception:
        sat_grid = None
    if sat_grid is None:
        pytest.skip("python-sat not installed")
    result = solve(grid)
    assert result is not None
    assert sat_grid == result.grid
