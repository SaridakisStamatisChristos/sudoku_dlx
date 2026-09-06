# v1.0 hardening audit

This document records the engineering changes used to promote `sudoku_dlx` from the 0.x series to a defensible v1.0 contract.

## Scope

The hardening pass preserves the existing bitset exact-cover architecture. It does not replace the solver with a different algorithm or native backend. Work focused on correctness, explicit semantics, reentrancy, deterministic validation, reproducible regression evidence, and release discipline.

## Correctness defects repaired

### Retaining the first solution while counting

The 0.x low-level search reused the live DFS path as the returned solution. With `limit=2`, a unique puzzle could find one solution, continue searching for a second, unwind the path, and then return an incomplete grid even though the count was correct.

v1 stores the first complete path independently before continuing the uniqueness search. Tests assert that `limit=2` returns a complete solution that preserves every given clue.

### Canonical representation ordering

Canonical search visits cells as nine 3×3 blocks because that enables useful prefix pruning. The earlier implementation returned that internal block-major key directly as an 81-character string, while public parsers interpret 81-character strings in row-major order. Re-parsing a canonical string could therefore change the puzzle and cause repeated canonicalization to cycle.

v1 keeps block-major ordering internal and converts the winning representative back to standard row-major order. Tests enforce validity, D4 invariance, and idempotence:

```python
c = canonical_form(grid)
assert canonical_form(from_string(c)) == c
```

### Shared mutable solver statistics

The compatibility engine previously routed public calls through one module-global `SOLVER` and then copied its mutable statistics. Concurrent calls could overwrite one another's counters.

v1 gives every public compatibility engine its own `BitDLX` instance. The old singleton remains exported only for compatibility with existing 0.x users. A threaded regression test verifies identical solutions and deterministic work counters across concurrent public calls.

### Backtrack accounting

0.x approximated backtracks as `branches - solution_count`. v1 records a failed branch when that recursive branch produces no new solution. Nodes, branches, backtracks, maximum depth, and solution count are therefore direct deterministic search-work counters.

## Input and API invariants

v1 validates:

- public grids are exactly 9×9 lists;
- cells are integers in `0..9`;
- existing givens do not conflict by row, column, or box;
- low-level clues have valid coordinates/values and conflicting duplicate clues are rejected;
- solution limits are integers ≥ 1.

`solve(invalid)` returns `None`; `count_solutions(invalid)` returns `0`; malformed analysis input returns a stable invalid report rather than failing downstream.

## Generator contract

The complete seed grid is produced by Sudoku-preserving permutations of a known valid Latin-pattern solution rather than by repeatedly solving partially randomized boards.

All returned puzzles are verified unique.

- `symmetry="none"`: single-cell removals.
- `symmetry="rot180"`: exact rotational clue-pattern symmetry.
- `symmetry="mix"`: rotational removals first, then single-cell cleanup when useful.
- `minimal=True` with `none` or `mix`: strict single-clue minimality.
- `minimal=True, symmetry="rot180"`: orbit-minimality while preserving exact rotational symmetry.

This avoids conflating strict single-clue minimality with symmetry-preserving minimality.

## Difficulty v3

The rating is a deterministic heuristic, not a human solving standard. v1 rates the canonical representative so Sudoku isomorphs receive the same score independent of call order or cache state.

Inputs are machine-independent:

- clue sparsity;
- exact-cover nodes;
- failed branches/backtracks;
- failed-branch ratio.

Wall-clock timing is not part of the score.

## Regression methodology

`bench/regression.py` runs a fixed checked-in corpus and compares an exact deterministic signature containing:

- bounded solution count;
- first complete solution;
- nodes;
- branches;
- backtracks;
- maximum depth.

Wall-clock milliseconds are printed for observation but excluded from CI pass/fail decisions because shared runner timing is noisy. See `bench/README.md` for the baseline-update policy.

## CI / release gates

The v1 branch requires:

- Linux tests on CPython 3.10–3.14;
- Windows and macOS core smoke tests;
- deterministic search-work regression check;
- strict MkDocs build;
- wheel and sdist build;
- `twine check`;
- clean wheel install/import;
- version/tag equality in the tag release workflow.

The heavier property-based profile remains in the nightly workflow.

## Compatibility

The normal package-level API is preserved. Existing compatibility exports such as `SOLVER`, `generate_minimal`, and legacy parser/string helpers remain available, but new code should prefer the package-level API.

The visible semantic changes are intentional correctness fixes: canonical strings are now valid row-major Sudoku grids, backtrack statistics are exact rather than approximate, and generator symmetry/minimality semantics are explicit.
