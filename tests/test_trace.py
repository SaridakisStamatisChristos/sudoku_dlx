from textwrap import dedent
import json
from sudoku_dlx import cli, from_string, to_string, solve, build_reveal_trace

PUZ = dedent(
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


def _apply_reveal(initial81: str, steps):
    grid = [list(initial81[r * 9 : (r + 1) * 9]) for r in range(9)]
    for step in steps:
        r, c, v = step["r"], step["c"], step["v"]
        grid[r][c] = str(v)
    return "".join("".join(row) for row in grid)


def test_build_reveal_trace_roundtrip():
    g = from_string(PUZ)
    res = solve(g)
    assert res is not None
    tr = build_reveal_trace(g, res.grid, res.stats)
    assert tr["kind"] == "solution_reveal"
    assert len(tr["initial"]) == 81 and len(tr["solution"]) == 81
    # replay steps produces the solved string
    after = _apply_reveal(tr["initial"], tr["steps"])
    assert after == tr["solution"]


def test_cli_solve_writes_trace(tmp_path):
    out = tmp_path / "trace.json"
    rc = cli.main(["solve", "--grid", PUZ, "--trace", str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["kind"] == "solution_reveal"
    assert "stats" in data and "steps" in data
    # steps must fill exactly the blanks from initial
    blanks = sum(1 for ch in data["initial"] if ch == ".")
    assert blanks == len(data["steps"])
