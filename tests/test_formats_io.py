from sudoku_dlx.formats import read_grids, write_grids, detect_format

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

def test_txt_csv_jsonl_roundtrip(tmp_path):
    ptxt = tmp_path / "a.txt"
    ptxt.write_text(PUZ + "\n" + PUZ + "\n", encoding="utf-8")
    grids = read_grids(str(ptxt), "txt")
    assert grids and grids[0] == PUZ
    pcsv = tmp_path / "b.csv"
    write_grids(str(pcsv), grids, "csv")
    grids2 = read_grids(str(pcsv), "csv")
    assert grids2 == grids
    pjsonl = tmp_path / "c.jsonl"
    write_grids(str(pjsonl), grids2, "jsonl")
    grids3 = read_grids(str(pjsonl), "jsonl")
    assert grids3 == grids

def test_detect_format_defaults_txt(tmp_path):
    assert detect_format("x.sdk") == "txt"
    assert detect_format("x.ndjson") == "jsonl"
    assert detect_format("x.unknown") == "txt"
