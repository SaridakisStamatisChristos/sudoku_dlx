# Python API

```python
from sudoku_dlx import (
  from_string, to_string, is_valid, solve, analyze, rate,
  count_solutions, generate, canonical_form, explain,
  build_reveal_trace, sat_solve
)
```

## Parsing
```python
g = from_string("53..7....6..195... ...")  # 81 chars; .,0,-,_ are blanks
s = to_string(g)                             # always 81 chars with dots for blanks
```

## Solve
```python
res = solve(g)  # None if unsolvable/invalid
res.grid        # 9x9 list of ints
res.stats.ms, res.stats.nodes, res.stats.backtracks
```

## Analyze
```python
analyze(g)  # dict: {valid, solvable, unique, givens, difficulty, stats{...}}
```

## Generate
```python
p = generate(seed=123, target_givens=30, minimal=True, symmetry="mix")
```

## Canonical form
```python
can = canonical_form(g)  # 81-char canonical string (isomorphism-invariant)
```

## Difficulty
```python
score = rate(g)  # [0, 10], deterministic (nodes/backtracks/gaps/fill)
```

## Explain (human steps)
```python
exp = explain(g, max_steps=200)
exp["steps"]     # list of {type, strategy, ...}
exp["progress"]  # 81-char after steps
exp["solution"]  # full solution string (if solvable)
```

## Trace (solution reveal)
```python
trace = build_reveal_trace(g, res.grid, res.stats)
# keys: version, kind, initial, solution, steps, stats
```

## SAT cross-check (optional)
```python
sat = sat_solve(g)   # requires python-sat; returns 9x9 grid or None
```
