import os
import tempfile

from sudoku_dlx import cli

S = (
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


def test_cli_dedupe_makes_unique_file():
    s180 = "".join(reversed(S))
    with tempfile.TemporaryDirectory() as tmpdir:
        infile = os.path.join(tmpdir, "in.txt")
        outfile = os.path.join(tmpdir, "out.txt")
        with open(infile, "w", encoding="utf-8") as handle:
            handle.write(S + "\n")
            handle.write(s180 + "\n")
        rc = cli.main(["dedupe", "--in", infile, "--out", outfile])
        assert rc == 0
        with open(outfile, "r", encoding="utf-8") as handle:
            lines = [line.strip() for line in handle if line.strip()]
        assert len(lines) == 1
