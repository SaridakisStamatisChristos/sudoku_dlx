# Python API

```python
from sudoku_dlx import (
    DIFFICULTY_VERSION,
    analyze,
    build_reveal_trace,
    canonical_form,
    count_solutions,
    explain,
    from_string,
    generate,
    is_valid,
    is_well_formed,
    rate,
    sat_solve,
    solve,
    to_string,
)
```

## Parsing and validation

```python
g = from_string("<81 characters>")  # 1..9; ., 0, -, _ are blanks
s = to_string(g)                     # row-major 81-char string; dots for blanks

is_well_formed(g)  # exactly 9x9, integer cells in 0..9
is_valid(g)        # well-formed + no duplicate givens in row/column/box
```

Malformed grids are rejected deterministically. `solve()` returns `None` for invalid grids and `count_solutions()` returns `0`.

## Solve

```python
res = solve(g)  # None if invalid or unsatisfiable
if res is not None:
    res.grid
    res.stats.ms
    res.stats.nodes
    res.stats.branches
    res.stats.backtracks
    res.stats.max_depth
```

The public solve path creates search state per invocation. Concurrent public callers therefore do not share mutable search statistics.

## Count solutions

```python
n = count_solutions(g, limit=2)
```

`limit` must be an integer ≥ 1. A limit of 2 is sufficient to distinguish unsatisfiable, unique, and non-unique puzzles without enumerating every solution.

## Analyze

```python
report = analyze(g)
# version, valid, givens, solvable, unique, difficulty,
# canonical, solution, stats
```

## Generate

```python
p = generate(seed=7331, target_givens=30, minimal=True, symmetry="mix")
```

`target_givens` is an approximate lower target. Supported symmetry values are `none`, `rot180`, and `mix`.

- `minimal=True` with `none` / `mix`: strict single-clue minimality.
- `minimal=True, symmetry="rot180"`: exact rotational clue-pattern symmetry plus orbit-minimality.

The generator verifies uniqueness before returning.

## Canonical form

```python
can = canonical_form(g)
assert canonical_form(from_string(can)) == can
```

The result is an ordinary **row-major** 81-character Sudoku string. Internally, canonical search uses a block-major key for pruning, but that internal ordering is never exposed as the public grid representation.

The canonicalization equivalence set includes D4 transforms, band/stack permutations, row/column permutations within bands/stacks, and digit relabeling.

## Difficulty

```python
print(DIFFICULTY_VERSION)  # "3"
score = rate(g)            # float in [0, 10]
```

Difficulty v3 is deterministic and machine-independent. It rates the canonical representative using clue sparsity and exact-cover search-work counters. Wall-clock time is deliberately excluded.

## Explain human-style steps

```python
exp = explain(g, max_steps=200)
exp["steps"]
exp["progress"]
exp["solution"]
```

Strategies include singles, locked candidates, pairs, triples, X-Wing, Swordfish, and simple coloring.

## Reveal trace

```python
trace = build_reveal_trace(g, res.grid, res.stats)
# keys: version, kind, initial, solution, steps, stats
```

The reveal trace is a stable presentation format, not a promise to expose internal cover/uncover operations.

## SAT cross-check (optional)

```python
sat = sat_solve(g)  # requires the `sat` optional dependency
```

SAT support provides an independent solving path for validation and interoperability.
