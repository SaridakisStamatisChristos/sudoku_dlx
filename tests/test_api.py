import pytest

from sudoku_dlx.api import (
    Stats,
    SolveResult,
    analyze,
    count_solutions,
    from_string,
    is_valid,
    solve,
    to_string,
)


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


def test_from_string_rejects_bad_length():
    with pytest.raises(ValueError, match="81 characters"):
        from_string("12345")


def test_from_string_rejects_out_of_range_digit():
    s = "1" * 80 + "٠"  # Arabic zero → isdigit() but out of range
    with pytest.raises(ValueError, match="digits must be 1..9"):
        from_string(s)


def test_from_string_rejects_bad_character():
    s = "." * 40 + "x" + "." * 40
    with pytest.raises(ValueError, match="bad char"):
        from_string(s)


def test_solve_rejects_invalid_grid():
    grid = [[0] * 9 for _ in range(9)]
    grid[0][0] = 5
    grid[0][1] = 5
    assert not is_valid(grid)
    assert solve(grid) is None


def test_count_solutions_honours_limit(monkeypatch):
    grid = from_string("123456789" + "." * 72)

    seen = []

    class FakeEngine:
        def count(self, rows, *, limit):
            seen.append(limit)
            return limit

    monkeypatch.setattr("sudoku_dlx.engine.build_ec_rows_from_grid", lambda g: [g])
    monkeypatch.setattr("sudoku_dlx.engine.DLXEngine", lambda: FakeEngine())
    monkeypatch.setattr("sudoku_dlx.rating.rate", lambda g: 3.5)
    monkeypatch.setattr("sudoku_dlx.canonical.canonical_form", lambda g: "C" * 81)

    assert count_solutions(grid, limit=1) == 1
    assert count_solutions(grid, limit=2) == 2
    assert seen == [1, 2]


def test_analyze_reports_invalid_grid():
    grid = [[0] * 9 for _ in range(9)]
    grid[0][0] = 7
    grid[0][1] = 7
    summary = analyze(grid)
    assert summary["valid"] is False
    assert summary["solvable"] is False
    assert summary["unique"] is False
    assert summary["solution"] is None
    assert summary["stats"] == {"ms": 0, "nodes": 0, "backtracks": 0}


def test_analyze_partial_grid_detects_non_unique_solution(monkeypatch):
    grid = from_string("123456789" + "." * 72)

    solved = from_string("123456789" + "987654321" + "456789123" + "." * 54)
    stats = Stats(ms=12.5, nodes=42, backtracks=7)

    def fake_count(target, limit=2):
        assert limit == 2
        return 2

    def fake_solve(target, collect_stats=True):
        assert collect_stats is True
        return SolveResult(grid=solved, stats=stats)

    monkeypatch.setattr("sudoku_dlx.api.count_solutions", fake_count)
    monkeypatch.setattr("sudoku_dlx.api.solve", fake_solve)
    monkeypatch.setattr("sudoku_dlx.rating.rate", lambda g: 4.0)
    monkeypatch.setattr("sudoku_dlx.canonical.canonical_form", lambda g: "K" * 81)

    summary = analyze(grid)
    assert summary["valid"] is True
    assert summary["solvable"] is True
    assert summary["unique"] is False
    assert summary["solution"] is not None
    assert len(summary["solution"]) == 81
    assert summary["stats"]["nodes"] >= 0
