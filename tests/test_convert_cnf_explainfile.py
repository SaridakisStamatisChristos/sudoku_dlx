import json

from sudoku_dlx import cli

PUZ = (
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)


def test_convert_txt_csv_roundtrip(tmp_path):
    ptxt = tmp_path / "p.txt"
    ptxt.write_text(PUZ + "\n" + PUZ + "\n", encoding="utf-8")
    pcsv = tmp_path / "p.csv"
    rc = cli.main(["convert", "--in", str(ptxt), "--out", str(pcsv)])
    assert rc == 0
    ptxt2 = tmp_path / "q.txt"
    rc = cli.main(["convert", "--in", str(pcsv), "--out", str(ptxt2)])
    assert rc == 0
    assert ptxt2.read_text(encoding="utf-8").strip().splitlines()[0] == PUZ


def test_to_cnf_writes_dimacs(tmp_path):
    out = tmp_path / "p.cnf"
    rc = cli.main(["to-cnf", "--grid", PUZ, "--out", str(out)])
    assert rc == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("p cnf ")
    assert all(line.endswith(" 0") or line.startswith("p ") for line in lines)


def test_explain_file_ndjson(tmp_path):
    ptxt = tmp_path / "p.txt"
    ptxt.write_text(PUZ + "\n", encoding="utf-8")
    out = tmp_path / "steps.ndjson"
    rc = cli.main(["explain-file", "--in", str(ptxt), "--out", str(out)])
    assert rc == 0
    data = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(data) == 1
    obj = data[0]
    assert "grid" in obj and "steps" in obj and "progress" in obj
