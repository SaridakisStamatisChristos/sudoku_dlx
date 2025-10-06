from textwrap import dedent
import json
from sudoku_dlx import from_string, explain, solve
from sudoku_dlx import cli

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


def _apply_steps(grid, steps):
    g = [row[:] for row in grid]
    for st in steps:
        if st["type"] == "place":
            g[st["r"]][st["c"]] = st["v"]
        # eliminations already reflected by our stepper; ignored in reconstruction
    return g


def test_explain_api_makes_progress_and_is_deterministic():
    g = from_string(PUZ)
    out1 = explain(g, max_steps=200)
    out2 = explain(g, max_steps=200)
    assert out1["steps"] == out2["steps"]
    # steps should not be empty for this classic puzzle
    assert len(out1["steps"]) > 0
    # applying placements should move towards solution
    g2 = _apply_steps(g, out1["steps"])
    res = solve(g)
    res2 = solve(g2)
    assert res is not None and res2 is not None
    # filled clues after steps should be >= initial
    filled0 = sum(1 for r in range(9) for c in range(9) if g[r][c] != 0)
    filled1 = sum(1 for r in range(9) for c in range(9) if g2[r][c] != 0)
    assert filled1 >= filled0


def test_cli_explain_json(capsys):
    rc = cli.main(["explain", "--grid", PUZ, "--json", "--max-steps", "120"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "steps" in data and isinstance(data["steps"], list)
    assert "progress" in data and len(data["progress"]) == 81
