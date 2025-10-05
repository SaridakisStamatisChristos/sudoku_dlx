import json
from sudoku_dlx import cli


def test_rate_file_json(tmp_path, capsys):
    p = tmp_path / "p.txt"
    grids = [
        "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79",
        "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79",
    ]
    p.write_text("\n".join(grids) + "\n", encoding="utf-8")
    rc = cli.main(["rate-file", "--in", str(p), "--json"])
    assert rc == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 2
    j = json.loads(out[0])
    assert "grid" in j and "score" in j
