#!/usr/bin/env python3
"""Deterministic search-work regression gate for the BitDLX engine."""
from __future__ import annotations
import argparse, json, platform, time
from pathlib import Path
from sudoku_dlx.solver import BitDLX, from_string, grid_clues, to_string
ROOT = Path(__file__).resolve().parent

def load_cases(path: Path) -> list[str]:
    cases = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        if len(text) != 81:
            raise ValueError(f"{path}:{n}: puzzle must contain 81 cells")
        from_string(text)
        cases.append(text)
    if not cases:
        raise ValueError("benchmark corpus is empty")
    return cases

def run_case(puzzle: str):
    solver = BitDLX()
    grid = from_string(puzzle)
    start = time.perf_counter_ns()
    count, solution = solver.count_solutions(grid_clues(grid), limit=2, prepass=True)
    ms = (time.perf_counter_ns() - start) / 1_000_000.0
    s = solver.stats
    return {"puzzle": puzzle, "count": count, "solution": None if solution is None else to_string(solution), "nodes": s.nodes, "branches": s.branches, "backtracks": s.backtracks, "max_depth": s.max_depth, "elapsed_ms": round(ms, 6)}

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases", type=Path, default=ROOT / "regression_cases.txt")
    p.add_argument("--baseline", type=Path, default=ROOT / "regression_baseline.json")
    p.add_argument("--emit", type=Path)
    a = p.parse_args()
    timed = [run_case(x) for x in load_cases(a.cases)]
    signature = {"schema": 1, "engine": "BitDLX", "prepass": True, "solution_limit": 2, "cases": [{k: v for k, v in x.items() if k != "elapsed_ms"} for x in timed]}
    print(json.dumps({"signature": signature, "timing_ms": [x["elapsed_ms"] for x in timed], "python": platform.python_version(), "platform": platform.platform()}, indent=2, sort_keys=True))
    if a.emit:
        a.emit.write_text(json.dumps(signature, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0
    expected = json.loads(a.baseline.read_text(encoding="utf-8"))
    if signature != expected:
        print("deterministic search-work signature changed; inspect before updating the baseline")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
