# Benchmarks and regression checks

The benchmark layer separates **correctness/search-work regressions** from **wall-clock measurements**.

## Deterministic regression gate

Run:

```bash
python bench/regression.py
```

`regression.py` solves the fixed corpus in `regression_cases.txt` with `BitDLX`, solution limit 2, and the naked-single prepass enabled. CI compares these machine-independent fields exactly against `regression_baseline.json`:

- solution count (capped at 2)
- first complete solution
- search nodes
- branches
- failed branches / backtracks
- maximum search depth

Elapsed milliseconds are printed for observation, but are **not** used as a pass/fail threshold. Shared GitHub runners are noisy; treating their wall time as a hard regression gate creates false failures. Search-work counters instead detect algorithmic changes reproducibly across supported Python versions and machines.

If an intentional algorithm change modifies the deterministic signature, inspect the diff first and then regenerate the baseline explicitly:

```bash
python bench/regression.py --emit bench/regression_baseline.json
python bench/regression.py
```

Do not update the baseline merely to make CI green.

## Throughput benchmark

For a larger puzzle file:

```bash
python bench/bench_file.py --in puzzles.txt
```

Record the Python version, CPU, operating system, puzzle corpus/commit, and command line whenever publishing timing claims. Report distributions (at least median and p95) rather than a single best run when comparing machines or implementations.

## Fuzz / generator smoke test

```bash
python bench/fuzz_quick.py -n 100
```

This exercises generated puzzles and is complementary to the deterministic regression corpus and property-based test suite.

## Benchmark policy

Performance claims in the project README should be tied to a reproducible corpus and environment. The repository intentionally avoids claims such as “fastest” or “state of the art” without a checked-in comparison harness and evidence that supports the exact claim.
