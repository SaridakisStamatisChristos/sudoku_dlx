from textwrap import dedent

import pytest

from sudoku_dlx import cli


def test_cli_help_option(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Sudoku DLX: solve, rate, and generate puzzles." in out


def test_cli_no_args_prints_help(capsys):
    exit_code = cli.main([])
    assert exit_code == 2
    out = capsys.readouterr().out
    assert "usage:" in out.lower()


def test_cli_solve_command(capsys):
    puzzle = dedent(
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

    exit_code = cli.main(["solve", "--grid", puzzle, "--pretty", "--stats"])
    assert exit_code == 0
    captured = capsys.readouterr()
    lines = [line for line in captured.out.strip().splitlines() if line.strip()]
    assert len(lines) == 9
    assert lines[0].split()[0] == "5"
    assert "# solved in" in captured.err


def test_cli_rate_command(capsys):
    puzzle = "53..7....6..195..." + "." * 63
    exit_code = cli.main(["rate", "--grid", puzzle])
    assert exit_code == 0
    out = capsys.readouterr().out.strip()
    assert out
    float(out)


def test_cli_generate_respects_seed(capsys):
    exit_code = cli.main(["gen", "--seed", "123", "--givens", "30"])
    assert exit_code == 0
    out1 = capsys.readouterr().out.strip()

    exit_code = cli.main(["gen", "--seed", "123", "--givens", "30"])
    assert exit_code == 0
    out2 = capsys.readouterr().out.strip()

    assert out1 == out2


def test_cli_solve_file(tmp_path, capsys):
    grid = "53..7....6..195..." + "." * 63
    file_path = tmp_path / "puzzle.txt"
    file_path.write_text(grid + "\n", encoding="utf-8")

    exit_code = cli.main(["solve", "--file", str(file_path)])
    assert exit_code == 0
    out = capsys.readouterr().out.strip()
    assert len(out) == 81
