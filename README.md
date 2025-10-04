# sudoku-dlx-bitset

Fast **Sudoku** solver & generator using **Algorithm X / Dancing Links** with **Python bitsets** + incremental cover.
Targets **minimal, unique** puzzles (17-clue hunt capable).

> © 2025 Stamatis-Christos Saridakis — MIT. Core algorithm: exact cover (Knuth). This implementation is original and bitset-based.

[![CI](https://github.com/<your-username>/sudoku-dlx-bitset/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-username>/sudoku-dlx-bitset/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/<your-username>/sudoku-dlx-bitset/branch/main/graph/badge.svg)](https://codecov.io/gh/<your-username>/sudoku-dlx-bitset)
[![PyPI version](https://img.shields.io/pypi/v/sudoku-dlx-bitset.svg)](https://pypi.org/project/sudoku-dlx-bitset/)
[![pages](https://img.shields.io/badge/GitHub%20Pages-demo-blue)](https://<your-username>.github.io/sudoku-dlx-bitset/)

## Features
- Bitset DLX (no pointer structs), precomputed 729×324 exact-cover matrix
- Reusable solver state for fast uniqueness checks
- Generator with symmetry knobs (`rot180`, `none`, `mix`) and aggressive thinning
- Cheap **naked-singles prepass** for speed; **search stats** exposed
- Clean CLI + tests + CI + pre-commit hooks + web demo

## Install (dev)
```bash
git clone https://github.com/<your-username>/sudoku-dlx-bitset.git
cd sudoku-dlx-bitset
python -m venv .venv && source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
pytest -q
```

## CLI

```bash
python -m sudoku_dlx --help
python -m sudoku_dlx generate --target 17 --symmetry none --seed 1337
python -m sudoku_dlx solve --grid "..3.2.6..9..3.5..1..18.64..81.29..7....8....67..82.5......."
# Batch:
python -m sudoku_dlx solve-file puzzles.txt      # one 81-char grid per line
python -m sudoku_dlx solve-dir datasets/         # solve *.txt in dir
```

## Library

```python
from sudoku_dlx.solver import (
    SOLVER, generate_minimal, print_grid, is_minimal,
    grid_clues, from_string, to_string, validate_grid
)

puz, sol = generate_minimal(target_clues=17, symmetry="mix", max_rounds=8000)
print_grid(puz)
cnt, solved = SOLVER.count_solutions(grid_clues(puz), limit=2)
```

### Stats & prepass

The solver runs a cheap **naked-singles** prepass by default. After a call:

```python
cnt, sol = SOLVER.count_solutions(grid_clues(grid), limit=2)  # prepass=True by default
print(SOLVER.stats)  # nodes, branches, max_depth, solutions
```

Disable with `prepass=False` to benchmark raw DLX.

### Hardness estimate

```python
from sudoku_dlx.solver import hardness_estimate, from_string
g = from_string("53..7....6..195....")
print(hardness_estimate(g))  # e.g., 3.8
```

## Roadmap

* Isomorph class canonicalization (reject equivalent puzzles)
* MUS/MCS-style minimality certificates

## License

MIT — see LICENSE.
