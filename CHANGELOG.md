# Changelog

All notable changes to this project are documented here.

## Unreleased

### Fixes

- Full logical runs now surface strategy contradictions through `LogicalResult.contradiction` instead of leaking an internal `RuntimeError` through `logical_solve()`, `human_rate()`, and rated generation.
- Candidate contradiction detection now includes missing digit support in rows, columns, and boxes, not only empty per-cell candidate sets.
- Human Difficulty v1 now assigns the intended weights to the actual `x_wing_row`, `x_wing_col`, `swordfish_row`, and `swordfish_col` move names.
- Default `generate_rated()` searches a deterministic difficulty-specific clue-count profile when `target_givens` is omitted, while explicit `target_givens` remains fixed across attempts.
- Rated generation never accepts an internally contradictory human-logic path as an `expert` match.
- Added executable seed-7331 rated-generation regressions plus a nightly exact-solver oracle sweep that checks every human placement/elimination against the unique DLX solution.

## [1.1.0] - 2026-09-06

### Human logic

- Promoted the persistent candidate engine into public `LogicalState` / `logical_solve()` APIs.
- Added versioned human difficulty scoring through `human_rate()` and `HumanRating`.
- Kept `explain()` backward-compatible while routing it through the reusable logical state engine.

### Smart generation

- Added `GenerationResult` metadata with solution, givens, symmetry/minimality mode, machine difficulty, and human difficulty.
- Added deterministic `generate_rated()` for bounded human-difficulty-targeted generation.
- Existing `generate()` behavior and uniqueness/minimality/symmetry contracts remain unchanged.

### Performance and reliability

- Replaced the unbounded machine-rating dictionary with a bounded 4096-entry LRU cache.
- `analyze()` now canonicalizes once and reuses that representation for machine difficulty.
- Added v1.1 integration/regression coverage for persistent logic, deterministic human rating, generation metadata, bounded cache behavior, and rated-generation retry semantics.

## [1.0.1] - 2026-09-06

### Fixes

- Fixed the human explanation engine so candidate eliminations persist across logical steps instead of being recomputed away from the unchanged grid.
- Placements now refresh only newly illegal candidates while preserving earlier logical eliminations.
- Added contradiction guards for impossible candidate states produced during a logical explanation run.
- Added regression coverage proving an elimination can enable a subsequent placement without being repeated or forgotten.

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
- `minimal=True, symmetry="rot180"` preserves exact rotational clue-pattern symmetry and enforces orbit-minimality.
- Added explicit validation for generator options and final uniqueness/symmetry invariants.

### Validation and performance discipline

- Added v1 invariant tests for retained solutions, prepass equivalence, canonical idempotence, malformed input, deterministic generation, and concurrent public solver calls.
- Added a checked-in deterministic regression corpus and search-work signature.
- Wall-clock benchmark measurements remain informational; shared-runner timing is not used as a flaky CI threshold.
- Expanded CI across CPython 3.10–3.14, Windows/macOS smoke tests, strict docs, distribution build checks, and clean wheel installation.

## [0.2.0] - 2025-10-05

- Added Sudoku isomorphism canonicalization across D4 transforms, band/stack permutations, inner row/column permutations, and digit relabeling.
- Added `sudoku-dlx dedupe` for dataset deduplication.
- Expanded canonicalization tests and CLI documentation.

## [0.1.0]

- Initial packaged solver/generator release.
