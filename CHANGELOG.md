# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-09-06

### Correctness

- Fixed `BitDLX.count_solutions(..., limit>1)` so the first complete solution is retained while the search continues to establish uniqueness.
- Made public `solve()` / `count_solutions()` calls reentrant by giving each compatibility engine its own `BitDLX` state instead of sharing mutable global search statistics.
- Replaced approximate backtrack accounting with deterministic failed-branch counters and exposed branches/max depth in solve statistics.
- Hardened grid, clue, and solution-limit validation.
- Fixed canonical serialization: the internal block-major search key is now converted back to a normal row-major Sudoku string before being returned.
- Made canonicalization idempotent and directly usable as a valid Sudoku grid representation.
- Reworked difficulty scoring so isomorphic puzzles are rated from the same canonical representative and timing is not part of the score.

### Generation semantics

- Replaced repeated partial solves used to construct a full grid with direct Sudoku-preserving permutations of a valid complete grid.
- Made `mix` distinct from `rot180`: it attempts rotational removals first and then permits single-cell cleanup.
- `minimal=True` with `none` or `mix` enforces strict single-clue minimality.
- `minimal=True, symmetry="rot180"` preserves exact rotational clue-pattern symmetry and enforces orbit-minimality (no full rotational clue orbit can be removed while retaining uniqueness).
- Added explicit validation for generator options and final uniqueness/symmetry invariants.

### Validation and performance discipline

- Added v1 invariant tests for retained solutions, prepass equivalence, canonical idempotence, malformed input, deterministic generation, and concurrent public solver calls.
- Added a checked-in deterministic regression corpus and search-work signature covering solution count, solution, nodes, branches, failed branches, and depth.
- Wall-clock benchmark measurements remain informational; shared-runner timing is not used as a flaky CI threshold.
- Expanded CI across CPython 3.10–3.14, Windows/macOS smoke tests, strict docs, distribution build checks, and clean wheel installation.

### Release metadata

- Promoted the package to `1.0.0` and production/stable metadata.
- Repaired `CITATION.cff` repository, author, version, and release metadata.
- Refreshed documentation to separate measured guarantees from unsupported performance superlatives.

## [0.2.0] - 2025-10-05

- Added Sudoku isomorphism canonicalization across D4 transforms, band/stack permutations, inner row/column permutations, and digit relabeling.
- Added `sudoku-dlx dedupe` for dataset deduplication.
- Expanded canonicalization tests and CLI documentation.

## [0.1.0]

- Initial packaged solver/generator release.
