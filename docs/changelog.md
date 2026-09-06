# Changelog highlights

For the complete release history, see the repository-level `CHANGELOG.md`.

## 1.1.0 — 2026-09-06

- Public persistent `LogicalState` / `logical_solve()` human-solving API.
- Separate deterministic human difficulty v1 with `easy` / `medium` / `hard` / `expert` bands.
- Difficulty-targeted generation and rich `GenerationResult` metadata.
- Bounded machine-rating cache and canonicalization reuse in `analyze()`.
- New v1.1 logical/generation integration regression coverage.

## 1.0.1 — 2026-09-06

- Human explanations preserve candidate eliminations across logical steps.
- Placements refresh legal candidates without resurrecting prior eliminations.
- Contradiction guards and elimination-to-placement regression coverage.

## 1.0.0 — 2026-09-06

- Correct first-solution retention while bounded counting continues to establish uniqueness.
- Reentrant public solver state and exact deterministic search-work counters.
- Row-major, valid, idempotent canonical representatives.
- Difficulty v3 based on canonicalized machine-independent search work.
- Explicit strict-minimal vs rotational orbit-minimal generator semantics.
- Deterministic search-work regression corpus and CI gate.
- Linux CPython 3.10–3.14 tests plus Windows/macOS smoke coverage.
- Distribution build/install checks and unified demo + MkDocs Pages deployment.

## 0.2.0 — 2025-10-05

- Isomorphism canonicalization and dataset deduplication.
- Expanded canonicalization tests and CLI documentation.

## 0.1.0

- Initial packaged bitset exact-cover solver/generator release.
