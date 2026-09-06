# sudoku_dlx

A deterministic **Sudoku exact-cover and logical-reasoning toolkit** built around Algorithm X-style search with Python integer bitsets. It solves and counts solutions, generates unique puzzles, canonicalizes Sudoku isomorphs, explains puzzles with persistent human-style logic, rates machine and human difficulty separately, processes datasets, and runs in the browser through Pyodide.

The project name retains “DLX” because the model and minimum-column search follow the exact-cover/Dancing Links tradition. The core does **not** use pointer-linked DLX nodes: the 729 candidate rows and 324 constraints are represented as compact Python bitsets with incremental cover operations.

> © 2025–2026 Stamatis-Christos Saridakis — MIT License.

[![CI](https://github.com/SaridakisStamatisChristos/sudoku_dlx/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SaridakisStamatisChristos/sudoku_dlx/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://SaridakisStamatisChristos.github.io/sudoku_dlx/docs/)
[![Codecov](https://codecov.io/gh/SaridakisStamatisChristos/sudoku_dlx/branch/main/graph/badge.svg)](https://codecov.io/gh/SaridakisStamatisChristos/sudoku_dlx)
[![License: MIT](https://img.shields.io/github/license/SaridakisStamatisChristos/sudoku_dlx.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/sudoku_dlx.svg)](https://pypi.org/project/sudoku_dlx/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-demo-blue)](https://saridakisstamatischristos.github.io/sudoku_dlx/)

## What is included

- **Exact-cover solver:** 729 candidate assignments × 324 Sudoku constraints, minimum-column branching, optional naked-single prepass, first-solution solving, bounded solution counting, and iteration over solutions.
- **Deterministic work statistics:** nodes, branches, failed branches/backtracks, maximum depth, and wall-clock time at the public API boundary.
- **Persistent logical solver:** reusable `LogicalState` / `logical_solve()` state with singles, locked candidates, pairs, triples, X-Wing, Swordfish, and simple coloring.
- **Two difficulty models:** machine Difficulty v3 from canonicalized exact-cover work, plus Human Difficulty v1 from deterministic logical techniques and workload.
- **Unique puzzle generator:** deterministic seeds, approximate target clue count, strict minimality, rotational symmetry, and mixed removal mode.
- **Smart generation:** rich `GenerationResult` metadata and bounded `generate_rated()` targeting of `easy`, `medium`, `hard`, or `expert` human difficulty.
- **Canonicalization:** D4 board transforms, band/stack permutations, row/column permutations inside bands/stacks, and digit relabeling. The returned canonical form is an ordinary **row-major 81-character Sudoku string** and is idempotent.
- **Human-style explainer:** backward-compatible `explain-1` output routed through the persistent logical state engine.
- **Independent SAT cross-check:** optional `python-sat` verification and DIMACS CNF export.
- **Dataset tools:** batch generation, rating, analysis/statistics, format conversion, canonical deduplication, and batch explanation.
- **Delivery:** typed Python package, CLI, tests/property tests, reproducible regression corpus, MkDocs, GitHub Pages/Pyodide demo, and release workflows.

## Install

From a checkout:

```bash
git clone https://github.com/SaridakisStamatisChristos/sudoku_dlx.git
cd sudoku_dlx
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
python -m pip install -e ".[dev]"
pytest -q
```

Optional independent SAT validation:

```bash
python -m pip install -e ".[sat]"
```

## Python API

```python
from sudoku_dlx import (
    canonical_form,
    count_solutions,
    from_string,
    generate,
    generate_rated,
    generate_result,
    human_rate,
    logical_solve,
    rate,
    solve,
    to_string,
)

puzzle = from_string(
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)

result = solve(puzzle)
assert result is not None
print(to_string(result.grid))
print(result.stats)  # ms, nodes, backtracks, branches, max_depth

assert count_solutions(puzzle, limit=2) == 1
print("machine difficulty:", rate(puzzle))
print("human difficulty:", human_rate(puzzle))
print("canonical:", canonical_form(puzzle))

logical = logical_solve(puzzle)
print(logical.solved, logical.hardest_strategy, len(logical.steps))

created = generate(seed=7331, target_givens=30, symmetry="mix")
assert count_solutions(created, limit=2) == 1

meta = generate_result(seed=7331, target_givens=30)
print(meta.machine_difficulty, meta.human_difficulty.label)

rated = generate_rated("hard", seed=7331, max_attempts=64)
print(rated.givens, rated.attempts, rated.human_difficulty)
```

Public `solve()` and `count_solutions()` calls own their search state, so concurrent callers do not share mutable solver statistics. The exported legacy `SOLVER` singleton remains for 0.x compatibility; new library code should prefer the public API or instantiate `BitDLX` directly when low-level control is required.

## Persistent human logic

`LogicalState` owns both the grid and the candidate matrix. Eliminations are therefore retained across later steps rather than reconstructed from the unchanged grid.

```python
from sudoku_dlx import LogicalState

state = LogicalState(puzzle)
first_move = state.step()
result = state.run(max_steps=500)

print(result.solved)
print(result.stalled)
print(result.hardest_strategy)
print(result.steps)
```

Placements intersect the existing candidate matrix with candidates legal under the new grid. This preserves previous logical eliminations while removing candidates invalidated by the placement. Contradictory candidate states are detected explicitly.

The current deterministic strategy stack is:

1. naked single
2. hidden single
3. locked candidates / box-line interactions
4. naked and hidden pairs
5. X-Wing
6. naked and hidden triples
7. Swordfish
8. simple coloring

The ordering is part of the reproducibility contract for Human Difficulty v1.

## Machine vs human difficulty

The two difficulty scores answer different questions and are intentionally versioned separately.

**Difficulty v3 (`rate`)** is a reproducible engineering heuristic derived from the canonical representative and machine-independent exact-cover search work: clue sparsity, nodes, failed branches, and failure ratio. Wall-clock timing is excluded. Its canonical score cache is bounded to 4096 entries in v1.1.

**Human Difficulty v1 (`human_rate`)** measures the built-in deterministic logical path. It reports:

- score in `[0, 10]`
- `easy`, `medium`, `hard`, or `expert`
- whether the built-in logical stack solved the puzzle completely
- step / placement / elimination counts
- hardest strategy reached

A valid puzzle that the current human strategy stack cannot finish is classified as `expert`; this means **expert relative to this implementation's strategy set**, not a universal Sudoku tournament standard.

## Generator semantics

The existing `generate()` API always verifies uniqueness before returning and is unchanged in v1.1.

| Configuration | Guarantee |
| --- | --- |
| `symmetry="none"` | single-cell removals |
| `symmetry="rot180"` | exact 180° clue-pattern symmetry |
| `symmetry="mix"` | rotational removals first, then optional single-cell cleanup |
| `minimal=True` with `none` / `mix` | strict single-clue minimality: removing any remaining clue destroys uniqueness |
| `minimal=True, symmetry="rot180"` | rotational **orbit-minimality**: no complete rotational clue orbit can be removed while preserving uniqueness |

Strict single-clue minimality and exact rotational symmetry are different constraints. The API does not silently break requested rotational symmetry in order to claim single-clue minimality.

`target_givens` is an approximate lower target rather than a promise that every seed can reach exactly that clue count while preserving the requested constraints.

## Smart generation in v1.1

`generate_result()` preserves normal generation semantics and adds reproducible metadata:

```python
meta = generate_result(
    seed=7331,
    target_givens=30,
    minimal=False,
    symmetry="mix",
)

meta.grid
meta.solution
meta.givens
meta.symmetry
meta.minimality
meta.machine_difficulty
meta.human_difficulty
```

`generate_rated()` searches a deterministic, bounded sequence of generated candidates until the requested human difficulty label is reached:

```python
rated = generate_rated(
    "medium",
    seed=7331,
    symmetry="mix",
    max_attempts=64,
)
```

With a fixed seed, the candidate sequence and result are deterministic. `max_attempts` prevents unbounded generation. If no matching puzzle is found, the function raises `RuntimeError`. The difficulty labels are heuristics tied to Human Difficulty v1, not guarantees about an external publisher's grading system.

## CLI

The existing CLI remains backward compatible:

```bash
sudoku-dlx --help

# Solve / inspect
sudoku-dlx solve --grid "<81chars>" --pretty --stats
sudoku-dlx check --grid "<81chars>" --json
sudoku-dlx rate --grid "<81chars>"

# Generate
sudoku-dlx gen --seed 7331 --givens 30 --pretty
sudoku-dlx gen --seed 7331 --givens 30 --minimal --symmetry rot180
sudoku-dlx gen-batch --out puzzles.txt --count 1000 --givens 30 --parallel 8

# Canonicalize and deduplicate isomorphic puzzles
sudoku-dlx canon --grid "<81chars>"
sudoku-dlx dedupe --in puzzles.txt --out unique.txt

# Human-style explanation and batch tooling
sudoku-dlx explain --grid "<81chars>" --json
sudoku-dlx explain-file --in puzzles.txt --out steps.ndjson --max-steps 200
sudoku-dlx rate-file --in puzzles.txt --csv ratings.csv
sudoku-dlx stats-file --in puzzles.txt --json stats.json --csv diff_hist.csv
sudoku-dlx convert --in puzzles.txt --out puzzles.csv

# SAT interoperability
sudoku-dlx to-cnf --grid "<81chars>" --out puzzle.cnf
sudoku-dlx solve --grid "<81chars>" --crosscheck sat
```

For a reveal trace suitable for the browser visualizer:

```bash
sudoku-dlx solve --grid "<81chars>" --trace out.json
```

## Canonicalization

`canonical_form(grid)` maps supported Sudoku-preserving isomorphs to one stable representative. The implementation separates the **internal block-major search key** used for prefix pruning from the **public row-major representation** returned to callers.

Useful invariants covered by tests include:

```python
c = canonical_form(puzzle)
assert canonical_form(from_string(c)) == c
```

and equality across D4 transforms, digit relabeling, band/stack permutations, and permitted inner row/column permutations.

## Analysis efficiency

`analyze()` reports validity, givens, solvability, uniqueness, machine difficulty, canonical form, solution, and search statistics. In v1.1 it computes the canonical representation once and feeds that same representation into the cached machine-difficulty path instead of canonicalizing the puzzle twice.

## Correctness and independent validation

The test suite covers ordinary and adversarial solver cases, invalid inputs, uniqueness, generation/minimality, canonicalization invariants, persistent logical state, human-rating determinism, smart-generation metadata, explanation strategies, file/CLI behavior, concurrency/reentrancy, and property-based generation checks. Optional SAT cross-checking supplies an independent solving path.

The nightly property workflow runs the heavier randomized/property profile separately from normal pull-request CI.

## Benchmarks and performance regression

Run the deterministic regression gate:

```bash
python bench/regression.py
```

The checked-in corpus records solution count/solution and deterministic search-work counters. CI compares those counters exactly. Wall-clock milliseconds are printed but are intentionally **not** a hard gate on shared runners.

For larger corpus timing:

```bash
python bench/bench_file.py --in puzzles.txt
```

See [`bench/README.md`](bench/README.md) for the methodology and rules for updating the baseline. Performance claims should identify the corpus, commit, Python version, OS, CPU, and command used; this project does not claim “fastest” or “state of the art” without reproducible comparative evidence.

## CI and release gates

Pull requests run:

- CPython 3.10–3.14 tests on Linux
- Windows and macOS core smoke tests
- deterministic search-work regression checks
- strict MkDocs build
- wheel + sdist build and `twine check`
- clean wheel installation/import

Tag releases additionally verify that `vX.Y.Z` matches `sudoku_dlx.__version__` before attaching distributions to a GitHub Release. PyPI publication remains an explicit/manual workflow.

## License and citation

MIT — see [`LICENSE`](LICENSE).

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).
