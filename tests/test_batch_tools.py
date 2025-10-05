from sudoku_dlx import cli


def test_gen_batch_and_rate_file(tmp_path):
    out = tmp_path / "puzzles.txt"
    rc = cli.main(
        [
            "gen-batch",
            "--out",
            str(out),
            "--count",
            "5",
            "--givens",
            "35",
            "--symmetry",
            "none",
        ]
    )
    assert rc == 0
    assert out.exists()
    lines = [ln.strip() for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 5
    rc = cli.main(["rate-file", "--in", str(out)])
    assert rc == 0
