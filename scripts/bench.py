import time, statistics as st
from sudoku_dlx.solver import SOLVER, from_string, grid_clues

PUZZLES = [
    "53..7....6..195... .98....6. 8...6...3 4..8.3..1 7...2...6 .6....28. ...419..5 ....8..79".replace(" ", ""),
    "..3.2.6..9..3.5..1..18.64..81.29..7....8....67..82.5.....1....23..7.9..5..8.3..",
]

def run_one(s):
    g = from_string(s)
    t0 = time.perf_counter()
    cnt, sol = SOLVER.count_solutions(grid_clues(g), limit=2)
    dt = (time.perf_counter() - t0) * 1000
    return cnt, dt, SOLVER.stats

def main():
    times = []
    for s in PUZZLES:
        cnt, dt, stats = run_one(s)
        times.append(dt)
        print(f"solutions={cnt}  time_ms={dt:.2f}  nodes={stats.nodes}  branches={stats.branches}  depth={stats.max_depth}")
    print(f"median_ms={st.median(times):.2f} avg_ms={st.mean(times):.2f}")

if __name__ == "__main__":
    main()
