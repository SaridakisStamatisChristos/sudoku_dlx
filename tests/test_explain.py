from textwrap import dedent
import importlib
import json

import pytest

from sudoku_dlx import cli, explain, from_string, solve

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
        # Candidate-only eliminations are intentionally ignored in grid reconstruction.
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


def test_explain_persists_candidate_eliminations_between_steps(monkeypatch):
    explain_module = importlib.import_module("sudoku_dlx.explain")
    grid = [[0] * 9 for _ in range(9)]
    elimination_calls = 0

    def fake_candidates(_grid):
        cand = [[set(range(1, 10)) for _ in range(9)] for _ in range(9)]
        cand[0][0] = {1, 2}
        return cand

    def fake_elimination(_grid, cand):
        nonlocal elimination_calls
        elimination_calls += 1
        if 2 not in cand[0][0]:
            return None
        cand[0][0].remove(2)
        return {
            "type": "eliminate",
            "strategy": "test_elimination",
            "r": 0,
            "c": 0,
            "remove": 2,
        }

    monkeypatch.setattr(explain_module, "candidates", fake_candidates)
    monkeypatch.setattr(explain_module, "_ELIMINATION_STRATEGIES", (fake_elimination,))
    monkeypatch.setattr(explain_module, "solve", lambda _grid: None)

    out = explain_module.explain(grid, max_steps=2)

    assert [step["type"] for step in out["steps"]] == ["eliminate", "place"]
    assert out["steps"][1]["strategy"] == "naked_single"
    assert out["progress"][0] == "1"
    assert elimination_calls == 1


def test_stateful_step_rejects_candidate_contradiction(monkeypatch):
    explain_module = importlib.import_module("sudoku_dlx.explain")
    grid = [[0] * 9 for _ in range(9)]
    cand = [[set(range(1, 10)) for _ in range(9)] for _ in range(9)]
    cand[0][0] = {1}

    def bad_elimination(_grid, state):
        state[0][0].remove(1)
        return {
            "type": "eliminate",
            "strategy": "bad_test_elimination",
            "r": 0,
            "c": 0,
            "remove": 1,
        }

    monkeypatch.setattr(explain_module, "_PLACEMENT_STRATEGIES", ())
    monkeypatch.setattr(explain_module, "_ELIMINATION_STRATEGIES", (bad_elimination,))

    with pytest.raises(RuntimeError, match="produced a contradiction"):
        explain_module._step_once_stateful(grid, cand)


def test_cli_explain_json(capsys):
    rc = cli.main(["explain", "--grid", PUZ, "--json", "--max-steps", "120"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "steps" in data and isinstance(data["steps"], list)
    assert "progress" in data and len(data["progress"]) == 81
