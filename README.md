# sudoku-dlx-bitset

Fast **Sudoku** solver & generator using **Algorithm X / Dancing Links** with **Python bitsets** + incremental cover.
Targets **minimal, unique** puzzles (17-clue hunt capable).

> © 2025 Stamatis-Christos Saridakis — MIT. Core algorithm: exact cover (Knuth). This implementation is original and bitset-based.

[![CI](https://github.com/SaridakisStamatisChristos/sudoku_dlx/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SaridakisStamatisChristos/sudoku_dlx/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/SaridakisStamatisChristos/sudoku_dlx/branch/main/graph/badge.svg)](https://codecov.io/gh/SaridakisStamatisChristos/sudoku_dlx)
[![License: MIT](https://img.shields.io/github/license/SaridakisStamatisChristos/sudoku_dlx.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/sudoku-dlx-bitset.svg)](https://pypi.org/project/sudoku-dlx-bitset/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-demo-blue)](https://SaridakisStamatisChristos.github.io/sudoku_dlx/)

## Features
- Bitset DLX (no pointer structs), precomputed 729×324 exact-cover matrix
- Reusable solver state for fast uniqueness checks
- Generator with symmetry knobs (`rot180`, `none`, `mix`) and aggressive thinning
- Cheap **naked-singles prepass** for speed; **search stats** exposed
- Clean CLI + tests + CI + pre-commit hooks + web demo

## Install (dev)
```bash
git clone https://github.com/SaridakisStamatisChristos/sudoku_dlx.git
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

## Publish to PyPI

This repository is already structured as a Python package (`src` layout, metadata in `pyproject.toml`).

### 1. Prepare your PyPI credentials

1. Sign in (or create an account) on [PyPI](https://pypi.org/) and optionally on [TestPyPI](https://test.pypi.org/).
2. Go to **Account settings ▸ API tokens ▸ Add API token**.
3. Give the token a descriptive name (for example `sudoku-dlx-bitset-publish`) and choose the project scope
   (selecting *Entire account* allows uploads for future projects, while *Project: sudoku-dlx-bitset* restricts it).
4. Copy the generated token immediately—PyPI only shows it once. The token will look like `pypi-AgENdGVzdC5weXBpLm9yZwIk...`.
5. Store it securely:
   * For local publishing, create a `~/.pypirc` file and set the token as the password:

     ```ini
     [pypi]
     username = __token__
     password = pypi-your-token-value

     [testpypi]
     username = __token__
     password = pypi-your-test-token-value
     ```

   * For GitHub Actions, add the token as an encrypted secret (e.g. `PYPI_API_TOKEN`) and pass it to `twine` using
     `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=${{ secrets.PYPI_API_TOKEN }}`.

### 2. Build the release artifacts

1. Update `pyproject.toml` with the new `version` and adjust the changelog/release notes.
2. Make sure the build backend is installed, then build the distribution artifacts:

   ```bash
   python -m pip install --upgrade build twine
   python -m build  # creates dist/*.tar.gz and dist/*.whl
   ```

### 3. Publish the release

1. (Optional) Upload to TestPyPI first to validate the release:

   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

2. Upload to the main PyPI index once satisfied:

   ```bash
   python -m twine upload dist/*
   ```

3. Tag the release in Git and push the tag so GitHub releases stay in sync.

The CI workflow already runs tests against multiple Python versions and uploads coverage
reports to Codecov; the `pages` workflow deploys the static demo from the `web/` directory.
