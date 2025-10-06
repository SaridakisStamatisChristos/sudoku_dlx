"""
Quick manual fuzz: generate and solve a bunch of puzzles.
Run locally:  python bench/fuzz_quick.py --n 50
"""
import argparse, random
from sudoku_dlx import generate, solve, count_solutions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--givens", type=int, default=34)
    ap.add_argument("--minimal", action="store_true")
    ns = ap.parse_args()
    rng = random.Random(42)
    ok = 0
    for i in range(ns.n):
        g = generate(
            seed=rng.randrange(2**31 - 1),
            target_givens=ns.givens,
            minimal=ns.minimal,
            symmetry="none",
        )
        # must be at least uniquely solvable
        assert count_solutions(g, limit=2) == 1
        res = solve([row[:] for row in g])
        assert res is not None
        ok += 1
    print(f"OK: {ok}/{ns.n}")


if __name__ == "__main__":
    main()
