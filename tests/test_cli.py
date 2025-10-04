import subprocess, sys

def test_cli_help():
    code = subprocess.call([sys.executable, "-m", "sudoku_dlx", "--help"])
    assert code == 0
