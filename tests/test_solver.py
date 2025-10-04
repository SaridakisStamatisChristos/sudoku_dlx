import pytest
from sudoku_dlx.solver import SOLVER, generate_minimal, grid_clues, is_minimal, set_seed

def test_solve_simple():
    s = ("53..7...."
         "6..195..."
         ".98....6."
         "8...6...3"
         "4..8.3..1"
         "7...2...6"
         ".6....28."
         "...419..5"
         "....8..79")
    grid = [[0]*9 for _ in range(9)]
    for i,ch in enumerate(s):
        r,c = divmod(i,9)
        grid[r][c] = 0 if ch=='.' else int(ch)
    cnt, sol = SOLVER.count_solutions(grid_clues(grid), limit=2)
    assert cnt == 1
    assert all(sol[r][c] in range(1,10) for r in range(9) for c in range(9))

def test_generate_unique():
    set_seed(12345)
    puz, sol = generate_minimal(target_clues=24, symmetry="mix")
    cnt, _ = SOLVER.count_solutions(grid_clues(puz), limit=2)
    assert cnt == 1
    clues = sum(1 for r in range(9) for c in range(9) if puz[r][c] != 0)
    assert clues <= 35
