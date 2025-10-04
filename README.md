# sudoku_dlx

Fast **Sudoku** solver & generator using **Algorithm X / Dancing Links (DLX)** with Python bitsets and an incremental cover model. Exposes timing & search stats for reproducible benchmarking. Runs in the browser via Pyodide (demo linked below).

> © 2025 Stamatis-Christos Saridakis — MIT. Core algorithm: exact cover (Knuth). This implementation is original and bitset-based.

[![CI](https://github.com/SaridakisStamatisChristos/sudoku_dlx/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SaridakisStamatisChristos/sudoku_dlx/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/SaridakisStamatisChristos/sudoku_dlx/branch/main/graph/badge.svg)](https://codecov.io/gh/SaridakisStamatisChristos/sudoku_dlx)
[![License: MIT](https://img.shields.io/github/license/SaridakisStamatisChristos/sudoku_dlx.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/sudoku_dlx.svg)](https://pypi.org/project/sudoku_dlx/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-demo-blue)](https://saridakisstamatischristos.github.io/sudoku_dlx/)

## Features
- Exact-cover Sudoku with **DLX** (no pointer structs; compact bitset encoding).
- **Stats exposed**: elapsed ms, node visits, backtracks.
- **Generator**: deterministic with `--seed`; removes clues while preserving **unique solvability** near a target clue count.
- **Difficulty rater**: quick heuristic in `[0, 10]` from givens + search effort.
- **CLI** (`sudoku-dlx`) + typed API + tests + CI + web demo.

> Note: Current generator aims for *unique* puzzles near `target_givens`; **minimality** and **symmetry options** are planned (see Roadmap).

## Install (dev)
```bash
git clone https://github.com/SaridakisStamatisChristos/sudoku_dlx.git
cd sudoku_dlx
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

## Publish to PyPI

This repository is already structured as a Python package (`src` layout, metadata in `pyproject.toml`).
To publish a new version on [PyPI](https://pypi.org/project/sudoku_dlx/):

1. Update `pyproject.toml` with the new `version` and adjust the changelog/release notes.
2. Make sure the build backend is installed, then build the distribution artifacts:

   ```bash
   python -m pip install --upgrade build twine
   python -m build  # creates dist/*.tar.gz and dist/*.whl
   ```

3. Upload the artifacts with [Twine](https://twine.readthedocs.io/):

   ```bash
   python -m twine upload dist/*
   ```

4. Tag the release in Git and push the tag so GitHub releases stay in sync.

The CI workflow already runs tests against multiple Python versions and uploads coverage
reports to Codecov; the `pages` workflow deploys the static demo from the `web/` directory.
