from sudoku_dlx.api import from_string, is_valid, solve, to_string


def test_parse_roundtrip():
    s = (
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
    grid = from_string(s)
    assert is_valid(grid)
    rebuilt = to_string(grid)
    assert len(rebuilt) == 81
    for i, ch in enumerate(s):
        if ch != ".":
            assert rebuilt[i] == ch


def test_stats_exposed():
    grid = [[0] * 9 for _ in range(9)]
    result = solve(grid)
    assert result is not None
    assert result.stats.nodes >= 0
    assert result.stats.backtracks >= 0
    assert result.stats.ms >= 0.0
