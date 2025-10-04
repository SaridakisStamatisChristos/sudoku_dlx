from __future__ import annotations
import argparse, sys, pathlib

from .solver import (
    SOLVER, generate_minimal, is_minimal, print_grid, grid_clues, set_seed,
)

def parse_grid(s: str):
    s = "".join(ch for ch in s if not ch.isspace())
    if len(s) != 81:
        raise ValueError("Grid must be 81 characters (digits 1-9 or . for empty)")
    g = [[0] * 9 for _ in range(9)]
    for i, ch in enumerate(s):
        r, c = divmod(i, 9)
        g[r][c] = 0 if ch == "." else int(ch)
    return g

def cmd_generate(args):
    set_seed(args.seed)
    puz, _sol = generate_minimal(
        target_clues=args.target,
        max_rounds=args.max_rounds,
        symmetry=args.symmetry,
        early_asymmetric=not args.no_early_asym,
    )
    print_grid(puz)

def cmd_solve(args):
    g = parse_grid(args.grid)
    cnt, solved = SOLVER.count_solutions(grid_clues(g), limit=2)
    print(f"Solutions: {cnt}")
    if solved:
        print("One solution:")
        print_grid(solved)

def cmd_solve_file(args):
    path = pathlib.Path(args.path)
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, 1):
        s = "".join(ch for ch in line.strip() if not ch.isspace())
        if not s:
            continue
        g = parse_grid(s)
        cnt, _ = SOLVER.count_solutions(grid_clues(g), limit=2)
        print(f"{path.name}:{i}: solutions={cnt}")

def cmd_solve_dir(args):
    d = pathlib.Path(args.dir)
    for p in sorted(d.glob("*.txt")):
        cmd_solve_file(argparse.Namespace(path=str(p)))

def main(argv=None):
    p = argparse.ArgumentParser(prog="sudoku-dlx", description="Sudoku DLX bitset solver/generator")
    sub = p.add_subparsers(dest="cmd")

    pg = sub.add_parser("generate", help="Generate a unique minimal-ish puzzle")
    pg.add_argument("--target", type=int, default=17)
    pg.add_argument("--max-rounds", type=int, default=8000)
    pg.add_argument("--symmetry", choices=["mix", "rot180", "none"], default="mix")
    pg.add_argument("--seed", type=int, default=None)
    pg.add_argument("--no-early-asym", action="store_true", help="Disable early asymmetric thinning")
    pg.set_defaults(func=cmd_generate)

    ps = sub.add_parser("solve", help="Solve a puzzle")
    ps.add_argument("--grid", required=True, help="81 chars with . for blanks")
    ps.set_defaults(func=cmd_solve)

    pf = sub.add_parser("solve-file", help="Solve puzzles from a text file (one line = one grid)")
    pf.add_argument("path")
    pf.set_defaults(func=cmd_solve_file)

    pd = sub.add_parser("solve-dir", help="Solve *.txt files in a directory")
    pd.add_argument("dir")
    pd.set_defaults(func=cmd_solve_dir)

    args = p.parse_args(argv)
    if not hasattr(args, "func"):
        p.print_help()
        return 2
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
