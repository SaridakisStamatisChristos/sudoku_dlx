from sudoku_dlx import cli, from_string


def _givens(s: str) -> int:
    return sum(1 for ch in s if ch != '.')


def test_gen_batch_bounds_parallel(tmp_path):
    out = tmp_path / "p.txt"
    rc = cli.main([
        "gen-batch",
        "--out", str(out),
        "--count", "6",
        "--givens", "34",
        "--min-givens", "30",
        "--max-givens", "40",
        "--parallel", "2",
        "--symmetry", "none",
    ])
    assert rc == 0
    lines = [ln.strip() for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 6
    for s in lines:
        g = _givens(s)
        assert 30 <= g <= 40
