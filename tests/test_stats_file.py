from sudoku_dlx import cli


def test_stats_file_small(tmp_path):
    puzzles = tmp_path / "p.txt"
    # make a tiny set
    grids = [
        "53..7....6..195... .98....6.8...6...3 4..8.3..17...2...6 .6....28... .419..5....8..79".replace(
            " ", ""
        ),
        "53..7....6..195... .98....6.8...6...3 4..8.3..17...2...6 .6....28... .419..5....8..79".replace(
            " ", ""
        ),
    ]
    puzzles.write_text("\n".join(grids) + "\n", encoding="utf-8")
    # ensure it runs and prints JSON
    rc = cli.main(["stats-file", "--in", str(puzzles)])
    assert rc == 0
