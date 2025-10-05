import argparse
import statistics as st
import sys
import time

from sudoku_dlx import from_string, solve


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark solve() on a file of puzzles (81-chars per line)."
    )
    parser.add_argument("--in", dest="in_path", required=True)
    ns = parser.parse_args()

    times: list[float] = []
    solved = 0
    with open(ns.in_path, "r", encoding="utf-8") as handle:
        for line in handle:
            s = "".join(ch for ch in line.strip() if not ch.isspace())
            if not s:
                continue
            grid = from_string(s)
            t0 = time.perf_counter()
            result = solve(grid)
            if result is None:
                continue
            times.append((time.perf_counter() - t0) * 1000)
            solved += 1
    if not times:
        print("no puzzles measured", file=sys.stderr)
        return 2
    mean = st.mean(times)
    p95 = st.quantiles(times, n=20)[-1]
    print(f"# puzzles: {solved} · mean {mean:.2f} ms · p95 {p95:.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
