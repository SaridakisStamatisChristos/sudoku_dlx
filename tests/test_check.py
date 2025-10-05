from textwrap import dedent
import json
from sudoku_dlx import analyze, from_string
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

def test_analyze_api_keys():
    g = from_string(PUZ)
    data = analyze(g)
    for k in ["version","valid","givens","solvable","unique","difficulty","canonical","solution","stats"]:
        assert k in data
    st = data["stats"]
    for k in ["ms","nodes","backtracks"]:
        assert k in st

def test_cli_check_pretty_and_json(capsys):
    rc = cli.main(["check", "--grid", PUZ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "valid:" in out and "difficulty:" in out and "canonical:" in out

    rc = cli.main(["check", "--grid", PUZ, "--json"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert data["valid"] is True
    assert "canonical" in data and len(data["canonical"]) == 81
    assert isinstance(data["difficulty"], float)
