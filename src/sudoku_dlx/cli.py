import argparse
import sys
from typing import Optional

from .api import from_string, is_valid, solve, to_string
from .generate import generate
from .rating import rate


def _read_grid_arg(ns: argparse.Namespace) -> str:
    if ns.grid:
        return ns.grid
    if ns.file:
        with open(ns.file, "r", encoding="utf-8") as handle:
            return "".join(handle.readlines())
    raise SystemExit("Provide --grid or --file")


def _print_grid(grid) -> None:
    for row in grid:
        print(" ".join(str(x) for x in row))


def cmd_solve(ns: argparse.Namespace) -> int:
    grid = from_string(_read_grid_arg(ns))
    if not is_valid(grid):
        print("Invalid puzzle (duplicate in row/col/box).", file=sys.stderr)
        return 2
    result = solve(grid)
    if result is None:
        print("No solution found.", file=sys.stderr)
        return 3
    if ns.pretty:
        _print_grid(result.grid)
    else:
        print(to_string(result.grid))
    if ns.stats:
        print(
            f"# solved in {result.stats.ms:.2f} ms · nodes {result.stats.nodes} · backtracks {result.stats.backtracks}",
            file=sys.stderr,
        )
    return 0


def cmd_rate(ns: argparse.Namespace) -> int:
    grid = from_string(_read_grid_arg(ns))
    print(rate(grid))
    return 0


def cmd_gen(ns: argparse.Namespace) -> int:
    grid = generate(seed=ns.seed, target_givens=ns.givens)
    if ns.pretty:
        _print_grid(grid)
    else:
        print(to_string(grid))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sudoku-dlx",
        description="Sudoku DLX: solve, rate, and generate puzzles.",
    )
    sub = parser.add_subparsers(dest="cmd")

    solve_parser = sub.add_parser("solve", help="solve a puzzle")
    solve_parser.add_argument("--grid", help="81-char string; 0/./- for blanks")
    solve_parser.add_argument("--file", help="path to a file with 9 lines of 9 chars")
    solve_parser.add_argument("--pretty", action="store_true", help="print 9x9 grid format")
    solve_parser.add_argument("--stats", action="store_true", help="print timing & node stats to stderr")
    solve_parser.set_defaults(func=cmd_solve)

    rate_parser = sub.add_parser("rate", help="estimate difficulty in [0,10]")
    rate_parser.add_argument("--grid", help="81-char string; 0/./- for blanks")
    rate_parser.add_argument("--file", help="path to a file with 9 lines of 9 chars")
    rate_parser.set_defaults(func=cmd_rate)

    gen_parser = sub.add_parser("gen", help="generate a puzzle")
    gen_parser.add_argument("--seed", type=int, default=None)
    gen_parser.add_argument("--givens", type=int, default=28, help="target number of clues (approx)")
    gen_parser.add_argument("--pretty", action="store_true")
    gen_parser.set_defaults(func=cmd_gen)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
