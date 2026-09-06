# Python API

```python
from sudoku_dlx import (
    DIFFICULTY_VERSION,
    HUMAN_DIFFICULTY_VERSION,
    GenerationResult,
    HumanRating,
    LogicalState,
    analyze,
    canonical_form,
    count_solutions,
    explain,
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
```

## Solve and count

```python
res = solve(g)
n = count_solutions(g, limit=2)
```

The public exact-cover path remains reentrant and unchanged in v1.1.

## Machine difficulty

```python
print(DIFFICULTY_VERSION)  # "3"
score = rate(g)            # deterministic float in [0, 10]
```

Difficulty v3 uses the canonical representative and exact-cover search-work counters. Its cache is bounded in v1.1, so long-running dataset processes do not grow an unbounded puzzle dictionary.

## Persistent human logic

```python
state = LogicalState(g)
move = state.step()
result = state.run(max_steps=500)

result.grid
result.steps
result.solved
result.stalled
result.contradiction
result.hardest_strategy
```

`LogicalState` owns both the grid and candidate matrix. Candidate eliminations therefore survive across later logical steps, while placements intersect the current candidate state with newly legal candidates.

For a one-shot run:

```python
result = logical_solve(g, max_steps=500)
```

The strategy stack includes singles, locked candidates, pairs, triples, X-Wing, Swordfish, and simple coloring.

## Human difficulty

```python
print(HUMAN_DIFFICULTY_VERSION)  # "1"
human = human_rate(g)

human.score
human.label               # easy | medium | hard | expert
human.solved_logically
human.steps
human.placements
human.eliminations
human.hardest_strategy
```

Human difficulty is deliberately separate from machine/search difficulty. It is deterministic and based on the strongest logical strategy reached plus logical workload. A valid puzzle that the built-in logical stack cannot finish is placed in the `expert` band.

## Explain compatibility layer

```python
exp = explain(g, max_steps=200)
```

`explain()` keeps its existing `explain-1` dictionary surface while delegating to the persistent logical state engine.

## Generation

Existing behavior is unchanged:

```python
p = generate(seed=7331, target_givens=30, minimal=True, symmetry="mix")
```

For metadata:

```python
meta = generate_result(seed=7331, target_givens=30)

meta.grid
meta.solution
meta.givens
meta.machine_difficulty
meta.human_difficulty
meta.symmetry
meta.minimality
```

For human-difficulty targeting:

```python
rated = generate_rated(
    "hard",
    seed=7331,
    symmetry="mix",
    max_attempts=64,
)
```

A fixed seed makes the candidate sequence deterministic. If `target_givens` is omitted, v1.1 uses a clue-count prior for the requested band. If no matching candidate is found within `max_attempts`, `generate_rated()` raises `RuntimeError` instead of looping indefinitely.

Generator uniqueness and minimality/symmetry guarantees are unchanged from v1.0.x.

## Analyze

```python
report = analyze(g)
```

v1.1 reuses one canonical representation internally for machine rating rather than canonicalizing the same puzzle twice.

## Canonical form

```python
can = canonical_form(g)
assert canonical_form(from_string(can)) == can
```

The public canonical value remains an ordinary row-major 81-character string.
