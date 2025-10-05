import json
from sudoku_dlx import cli


def test_stats_file_limit_and_sample(tmp_path, capsys):
    # prepare 10 puzzles
    out = tmp_path / "p.txt"
    rc = cli.main(["gen-batch", "--out", str(out), "--count", "10", "--givens", "34", "--symmetry", "none"])
    assert rc == 0
    # limit=5
    rc = cli.main(["stats-file", "--in", str(out), "--limit", "5"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["count"] == 5
    # sample=4 (no limit)
    rc = cli.main(["stats-file", "--in", str(out), "--sample", "4"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["count"] == 4
