from textwrap import dedent

import pytest

from sudoku_dlx import cli


def test_cli_help_option(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Sudoku DLX bitset solver" in out


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

    exit_code = cli.main(["solve", "--grid", puzzle])
    assert exit_code is None
    out = capsys.readouterr().out
    assert "Solutions: 1" in out
    assert out.count("+-------") >= 4


def test_cli_generate_respects_seed(monkeypatch):
    calls = []

    def fake_print_grid(grid):
        calls.append(grid)

    monkeypatch.setattr(cli, "print_grid", fake_print_grid)
    exit_code = cli.main(["generate", "--target", "22", "--seed", "123", "--symmetry", "rot180"])
    assert exit_code is None
    assert calls, "print_grid should have been called"


def test_cli_solve_file_and_dir(tmp_path, capsys):
    grid = "53..7....6..195..." + "." * 63
    file_path = tmp_path / "puzzles.txt"
    file_path.write_text(grid + "\n", encoding="utf-8")

    exit_code_file = cli.main(["solve-file", str(file_path)])
    assert exit_code_file is None

    out = capsys.readouterr().out
    assert "puzzles.txt:1" in out

    exit_code_dir = cli.main(["solve-dir", str(tmp_path)])
    assert exit_code_dir is None
