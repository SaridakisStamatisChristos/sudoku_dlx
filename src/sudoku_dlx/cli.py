from __future__ import annotations

import argparse, sys, pathlib, csv, random, json, time, multiprocessing as mp
from typing import Optional

from .api import analyze, build_reveal_trace, from_string, is_valid, solve, to_string
from .explain import explain
from .canonical import canonical_form
from .generate import generate
from .rating import rate
from statistics import mean


def _count_givens(grid) -> int:
    return sum(1 for r in range(9) for c in range(9) if grid[r][c] != 0)


def _gen_batch_worker(args: tuple[int, int, bool, str, int, int]) -> str:
    seed_i, target_givens, minimal, symmetry, min_givens, max_givens = args
    local_rng = random.Random(seed_i)
    while True:
        g = generate(
            seed=local_rng.randrange(2**31 - 1),
            target_givens=target_givens,
            minimal=minimal,
            symmetry=symmetry,
        )
        gv = _count_givens(g)
        if min_givens <= gv <= max_givens:
            return canonical_form(g)



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


def _print_analysis(data: dict) -> None:
    def yes(b: bool) -> str:
        return "yes" if b else "no"

    print("== sudoku-dlx check ==")
    print(f"valid:     {yes(data['valid'])}   givens: {data['givens']}")
    print(f"solvable:  {yes(data['solvable'])}   unique: {yes(data['unique'])}")
    print(f"difficulty:{data['difficulty']:.1f}")
    stats = data["stats"]
    print(
        f"stats:     {stats['ms']} ms · nodes {stats['nodes']} · backtracks {stats['backtracks']}"
    )
    print(f"canonical: {data['canonical']}")
    if data["solution"]:
        print(f"solution:  {data['solution']}")


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
    if ns.trace:
        trace = build_reveal_trace(grid, result.grid, result.stats)
        outp = pathlib.Path(ns.trace)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(trace, indent=2, sort_keys=True), encoding="utf-8")
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


def cmd_check(ns: argparse.Namespace) -> int:
    grid = from_string(_read_grid_arg(ns))
    data = analyze(grid)
    if ns.json:
        print(json.dumps(data, separators=(",", ":"), sort_keys=True))
    else:
        _print_analysis(data)
    return 0


def cmd_explain(ns: argparse.Namespace) -> int:
    grid = from_string(_read_grid_arg(ns))
    data = explain(grid, max_steps=ns.max_steps)
    if ns.json:
        print(json.dumps(data, separators=(",", ":"), sort_keys=True))
    else:
        print("== sudoku-dlx explain ==")
        for i, step in enumerate(data["steps"], 1):
            print(f"{i:03d}. {step['strategy']}: {step}")
        print(f"solved: {data['solved']}  steps: {len(data['steps'])}")
    return 0


def cmd_gen(ns: argparse.Namespace) -> int:
    grid = generate(
        seed=ns.seed,
        target_givens=ns.givens,
        minimal=ns.minimal,
        symmetry=ns.symmetry,
    )
    if ns.pretty:
        _print_grid(grid)
    else:
        print(to_string(grid))
    return 0


def cmd_canon(ns: argparse.Namespace) -> int:
    grid = from_string(_read_grid_arg(ns))
    print(canonical_form(grid))
    return 0


def cmd_gen_batch(ns: argparse.Namespace) -> int:
    """
    Generate many canonicalized, unique puzzles quickly.
    """
    outp = pathlib.Path(ns.out)
    seen: set[str] = set()
    uniq: list[str] = []

    base_seed = ns.seed if ns.seed is not None else random.randrange(2**31 - 1)
    if ns.parallel <= 1:
        i = 0
        while len(uniq) < ns.count:
            args = (base_seed + i, ns.givens, ns.minimal, ns.symmetry, ns.min_givens, ns.max_givens)
            i += 1
            c = _gen_batch_worker(args)
            if c in seen:
                continue
            seen.add(c)
            uniq.append(c)
    else:
        with mp.Pool(processes=ns.parallel) as pool:
            i = 0
            # produce candidates until we reach count
            while len(uniq) < ns.count:
                batch_n = max(4 * ns.parallel, ns.count - len(uniq))
                seeds = [base_seed + j for j in range(i, i + batch_n)]
                i += batch_n
                args_iter = [
                    (seed, ns.givens, ns.minimal, ns.symmetry, ns.min_givens, ns.max_givens)
                    for seed in seeds
                ]
                for c in pool.imap_unordered(_gen_batch_worker, args_iter):
                    if c in seen:
                        continue
                    seen.add(c)
                    uniq.append(c)
                    if len(uniq) >= ns.count:
                        break
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8") as f:
        for u in uniq:
            f.write(u + "\n")
    print(f"# generated: {len(uniq)}", file=sys.stderr)
    return 0

def cmd_rate_file(ns: argparse.Namespace) -> int:
    inp = pathlib.Path(ns.in_path)
    rows: list[tuple[str, float]] = []
    with inp.open("r", encoding="utf-8") as handle:
        for line in handle:
            s = "".join(ch for ch in line.strip() if not ch.isspace())
            if not s:
                continue
            score = rate(from_string(s))
            rows.append((s, score))
            if ns.json:
                print(json.dumps({"grid": s, "score": round(score, 1)}, separators=(",", ":")))
            else:
                print(f"{score:.1f}")
    if ns.csv_path:
        with open(ns.csv_path, "w", newline="", encoding="utf-8") as csv_handle:
            writer = csv.writer(csv_handle)
            writer.writerow(["grid", "score"])
            writer.writerows(rows)
    return 0


def _percentile(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def cmd_stats_file(ns: argparse.Namespace) -> int:
    inp = pathlib.Path(ns.in_path)
    processed = 0
    n_valid = n_solvable = n_unique = 0
    givens: list[int] = []
    diffs: list[float] = []
    ms_list: list[float] = []
    t0 = time.perf_counter()
    # reservoir sample if requested
    sample_k = ns.sample if ns.sample and ns.sample > 0 else 0
    rng = random.Random(1337)
    lines: list[str] = []
    with inp.open("r", encoding="utf-8") as handle:
        for line in handle:
            s = "".join(ch for ch in line.strip() if not ch.isspace())
            if not s:
                continue
            if ns.limit and processed >= ns.limit:
                break
            processed += 1
            if sample_k == 0:
                lines.append(s)
            else:
                if len(lines) < sample_k:
                    lines.append(s)
                else:
                    j = rng.randrange(1, processed + 1)
                    if j <= sample_k:
                        lines[j - 1] = s
    for s in lines:
        try:
            grid = from_string(s)
        except Exception:
            continue
        data = analyze(grid)
        if data["valid"]:
            n_valid += 1
        if data["solvable"]:
            n_solvable += 1
        if data["unique"]:
            n_unique += 1
        givens.append(int(data["givens"]))
        diffs.append(float(data["difficulty"]))
        ms_list.append(float(data["stats"]["ms"]))
    if len(lines) == 0:
        print("no puzzles read", file=sys.stderr)
        return 2
    elapsed = (time.perf_counter() - t0) * 1000.0
    report = {
        "count": len(lines),
        "valid_pct": round(100.0 * n_valid / len(lines), 2),
        "solvable_pct": round(100.0 * n_solvable / len(lines), 2),
        "unique_pct": round(100.0 * n_unique / len(lines), 2),
        "givens_mean": round(mean(givens), 2),
        "givens_min": min(givens),
        "givens_max": max(givens),
        "difficulty_mean": round(mean(diffs), 3),
        "difficulty_p50": round(_percentile(diffs, 0.50), 3),
        "difficulty_p90": round(_percentile(diffs, 0.90), 3),
        "difficulty_p99": round(_percentile(diffs, 0.99), 3),
        "solve_ms_mean": round(mean(ms_list), 2),
        "elapsed_ms": round(elapsed, 1),
    }
    print(json.dumps(report, separators=(",", ":"), sort_keys=True))
    if ns.json_path:
        pathlib.Path(ns.json_path).write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
        )
    if ns.csv_path:
        bins = max(1, ns.bins)
        lo, hi = 0.0, 10.0
        width = (hi - lo) / bins
        counts = [0] * bins
        for diff in diffs:
            if diff < lo:
                idx = 0
            elif diff >= hi:
                idx = bins - 1
            else:
                idx = int((diff - lo) // width)
            counts[idx] += 1
        with open(ns.csv_path, "w", newline="", encoding="utf-8") as csv_handle:
            writer = csv.writer(csv_handle)
            writer.writerow(["bin_lower", "bin_upper", "count"])
            for i, count in enumerate(counts):
                writer.writerow(
                    [
                        round(lo + i * width, 3),
                        round(lo + (i + 1) * width, 3),
                        count,
                    ]
                )
    return 0

def cmd_dedupe(ns: argparse.Namespace) -> int:
    inp = pathlib.Path(ns.in_path)
    outp = pathlib.Path(ns.out_path)
    seen: set[str] = set()
    uniq: list[str] = []
    with inp.open("r", encoding="utf-8") as handle:
        for line in handle:
            s = "".join(ch for ch in line.strip() if not ch.isspace())
            if not s:
                continue
            try:
                grid = from_string(s)
            except Exception:
                continue
            canon = canonical_form(grid)
            if canon not in seen:
                seen.add(canon)
                uniq.append(canon)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8") as handle:
        for value in uniq:
            handle.write(value + "\n")
    print(f"# unique: {len(uniq)}", file=sys.stderr)
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
    solve_parser.add_argument("--trace", help="write a solution-reveal trace JSON to this path")
    solve_parser.set_defaults(func=cmd_solve)

    rate_parser = sub.add_parser("rate", help="estimate difficulty in [0,10]")
    rate_parser.add_argument("--grid", help="81-char string; 0/./- for blanks")
    rate_parser.add_argument("--file", help="path to a file with 9 lines of 9 chars")
    rate_parser.set_defaults(func=cmd_rate)

    check_parser = sub.add_parser(
        "check", help="validate/score a puzzle and show stats/canonical form"
    )
    check_parser.add_argument("--grid", help="81-char string; 0/./- for blanks")
    check_parser.add_argument("--file", help="path to a file with 9 lines of 9 chars")
    check_parser.add_argument("--json", action="store_true", help="output JSON")
    check_parser.set_defaults(func=cmd_check)

    explain_parser = sub.add_parser(
        "explain", help="human-style steps (naked/hidden single, locked candidates)"
    )
    explain_parser.add_argument("--grid", help="81-char string; 0/./- for blanks")
    explain_parser.add_argument("--file", help="path to a file with 9 lines of 9 chars")
    explain_parser.add_argument("--json", action="store_true")
    explain_parser.add_argument("--max-steps", type=int, default=200)
    explain_parser.set_defaults(func=cmd_explain)

    canon_parser = sub.add_parser(
        "canon",
        help=(
            "print canonical 81-char form (D4 × bands/stacks × inner row/col swaps × digit relabel)"
        ),
    )
    canon_parser.add_argument("--grid", help="81-char string; 0/./- for blanks")
    canon_parser.add_argument("--file", help="path to a file with 9 lines of 9 chars")
    canon_parser.set_defaults(func=cmd_canon)

    dedupe_parser = sub.add_parser(
        "dedupe", help="dedupe puzzles by canonical form (one 81-char grid per line)"
    )
    dedupe_parser.add_argument("--in", dest="in_path", required=True, help="input text file")
    dedupe_parser.add_argument(
        "--out", dest="out_path", required=True, help="output file for unique canonical grids"
    )
    dedupe_parser.set_defaults(func=cmd_dedupe)

    genb_parser = sub.add_parser("gen-batch", help="generate N unique puzzles to a file")
    genb_parser.add_argument("--out", required=True, help="output file (81-char per line)")
    genb_parser.add_argument("--count", type=int, default=100, help="number of puzzles")
    genb_parser.add_argument("--givens", type=int, default=30)
    genb_parser.add_argument(
        "--symmetry", choices=["none", "rot180", "mix"], default="mix"
    )
    genb_parser.add_argument("--minimal", action="store_true")
    genb_parser.add_argument("--seed", type=int, default=None)
    genb_parser.add_argument("--min-givens", type=int, default=0, help="keep only puzzles with >= this many givens")
    genb_parser.add_argument("--max-givens", type=int, default=81, help="keep only puzzles with <= this many givens")
    genb_parser.add_argument("--parallel", type=int, default=1, help="processes for generation (default 1)")
    genb_parser.set_defaults(func=cmd_gen_batch)

    ratef_parser = sub.add_parser("rate-file", help="rate each puzzle in a file")
    ratef_parser.add_argument("--in", dest="in_path", required=True)
    ratef_parser.add_argument(
        "--csv", dest="csv_path", help="optional CSV output path"
    )
    ratef_parser.add_argument("--json", action="store_true", help="print one JSON object per line to stdout")
    ratef_parser.set_defaults(func=cmd_rate_file)

    stats_parser = sub.add_parser("stats-file", help="summarize a file of puzzles")
    stats_parser.add_argument(
        "--in", dest="in_path", required=True, help="input text file (81-char per line)"
    )
    stats_parser.add_argument("--json", dest="json_path", help="write JSON report to file")
    stats_parser.add_argument(
        "--csv", dest="csv_path", help="write difficulty histogram CSV"
    )
    stats_parser.add_argument(
        "--bins", type=int, default=11, help="histogram bins (default 11 for 0..10)"
    )
    stats_parser.add_argument("--limit", type=int, default=0, help="process at most N lines (0 = no limit)")
    stats_parser.add_argument("--sample", type=int, default=0, help="reservoir sample K lines (0 = no sampling)")
    stats_parser.set_defaults(func=cmd_stats_file)

    gen_parser = sub.add_parser("gen", help="generate a puzzle")
    gen_parser.add_argument("--seed", type=int, default=None)
    gen_parser.add_argument("--givens", type=int, default=28, help="target number of clues (approx)")
    gen_parser.add_argument(
        "--minimal",
        action="store_true",
        help="enforce minimality (slower)",
    )
    gen_parser.add_argument(
        "--symmetry",
        choices=["none", "rot180", "mix"],
        default="mix",
        help="apply symmetry during clue removal",
    )
    gen_parser.add_argument("--pretty", action="store_true")
    gen_parser.set_defaults(func=cmd_gen)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
