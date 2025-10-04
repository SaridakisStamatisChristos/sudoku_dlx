from sudoku_dlx.solver import from_string, to_string, validate_grid, grid_clues, SOLVER

def test_parse_roundtrip():
    s = ("53..7...."
         "6..195..."
         ".98....6."
         "8...6...3"
         "4..8.3..1"
         "7...2...6"
         ".6....28."
         "...419..5"
         "....8..79")
    g = from_string(s)
    assert validate_grid(g)
    s2 = to_string(g)
    assert len(s2) == 81
    for i, ch in enumerate(s):
        if ch != ".":
            assert s2[i] == ch

def test_stats_exposed():
    g = [[0]*9 for _ in range(9)]
    cnt, _ = SOLVER.count_solutions(grid_clues(g), limit=1)
    assert cnt >= 1 or cnt == 0
    assert SOLVER.stats.nodes > 0
