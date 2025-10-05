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
sudoku-dlx --help

# Solve (single grid as 81 chars; '.' or '0' for blanks)
sudoku-dlx solve --grid "..3.2.6..9..3.5..1..18.64..81.29..7....8....67..82.5......."
sudoku-dlx solve --file puzzles.txt               # a file with 9 lines of 9 chars
sudoku-dlx solve --grid "<81chars>" --pretty --stats

# Rate difficulty (0..10)
sudoku-dlx rate  --grid "<81chars>"

# Canonicalize (dedupe isomorphic puzzles)
sudoku-dlx canon --grid "<81chars>"  # D4 × bands/stacks × inner row/col × digit relabel
# Produces a stable 81-char string for deduping datasets.

# Batch tools
sudoku-dlx gen-batch --out puzzles.txt --count 1000 --givens 30 --symmetry rot180 --minimal
sudoku-dlx rate-file --in puzzles.txt --csv ratings.csv
python bench/bench_file.py --in puzzles.txt

# Dedupe a file of puzzles (fast)
sudoku-dlx dedupe --in puzzles.txt --out unique.txt

# Generate a unique puzzle (deterministic with seed)
sudoku-dlx gen   --seed 123 --givens 30           # ~target clue count (approx)
sudoku-dlx gen   --seed 123 --givens 30 --pretty
# Analyze (valid/solvable/unique/difficulty/stats/canonical)
sudoku-dlx check --grid "<81chars>"
sudoku-dlx check --grid "<81chars>" --json > report.json

# Dataset stats
sudoku-dlx stats-file --in puzzles.txt --json stats.json --csv diff_hist.csv
# prints a compact JSON summary to stdout and writes optional files:
# {
#   "count": 1000, "valid_pct": 100.0, "solvable_pct": 100.0, "unique_pct": 100.0,
#   "givens_mean": 29.4, "difficulty_mean": 4.2, "difficulty_p90": 6.8, ...
# }

# Advanced generator flags:
# Minimal & symmetry (slower; strict guarantee)
sudoku-dlx gen   --seed 123 --givens 28 --minimal
sudoku-dlx gen   --seed 123 --givens 28 --minimal --symmetry rot180

# Trace & Visualize
sudoku-dlx solve --grid "<81chars>" --trace out.json
# Then open web/visualizer.html in your browser and load out.json
# (works on GitHub Pages)
```

What this gives you

Strict minimality: after generation, removing any single clue breaks uniqueness.

Symmetry enforcement: rot180 removals are paired; mix keeps pairs adjacent but allows singles too.

CI-safe tests: fast settings, strong assertions.

## Library (typed API)

```python
from sudoku_dlx import from_string, to_string, is_valid, solve, generate, rate

# Parse and validate
g = from_string("53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79")
assert is_valid(g)

# Solve with stats
res = solve(g)
if res is not None:
    print("Solved (ms, nodes, backtracks):", res.stats.ms, res.stats.nodes, res.stats.backtracks)
    print("Solution (81 chars):", to_string(res.grid))

# Generate a unique puzzle near a target clue count
p = generate(seed=42, target_givens=30)

# Difficulty score in [0,10]
print("difficulty:", rate(p))
```

### Stats

`solve()` returns `SolveResult(stats=Stats(ms, nodes, backtracks))`. These are also used by the rater.

### Difficulty rating

```python
from sudoku_dlx import rate, from_string
g = from_string("53..7....6..195...." + "."*63)
print(rate(g))  # e.g., 3.8
```

## Roadmap

* Minimality guarantee and symmetry knobs for the generator
* Isomorph class canonicalization (reject equivalent puzzles)
* Optional DLX step recorder + visualizer
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

### Automated releases (no auto-PyPI)
On pushing a tag like `v0.2.1`, GitHub Actions will:
- run tests against 3.10–3.12,
- build wheels/sdist, and
- attach artifacts to the GitHub Release (no PyPI upload).

### Manual publish (when you’re ready)
1. Create a token on PyPI (or TestPyPI).
2. Add a repo secret:
   - **Settings → Secrets and variables → Actions**
   - New secrets: `PYPI_API_TOKEN` (and/or `TEST_PYPI_API_TOKEN`)
3. From **Actions** tab, run **publish**:
   - Choose **pypi** or **testpypi**
   - Optionally set **ref** (leave blank to use default branch HEAD)
4. The workflow builds and uploads the current code to the chosen index.
