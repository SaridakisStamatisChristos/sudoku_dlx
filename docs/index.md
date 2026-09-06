# Sudoku DLX

A deterministic Sudoku exact-cover toolkit using **Algorithm X-style minimum-column search with Python integer bitsets**. The core represents 729 candidate assignments against 324 Sudoku constraints; it does not use pointer-linked Dancing Links nodes.

The package includes solving and bounded solution counting, unique puzzle generation, difficulty v3, Sudoku-isomorphism canonicalization, human-style explanation, dataset tooling, SAT cross-checking, and a Pyodide browser demo.

**Repo:** [:octicons-mark-github-16: GitHub](https://github.com/SaridakisStamatisChristos/sudoku_dlx) · **Demo:** [GitHub Pages](https://saridakisstamatischristos.github.io/sudoku_dlx/) · **v1 audit:** [hardening notes](V1_HARDENING.md)

## v1.0 guarantees

- Reentrant package-level solve/count APIs with deterministic nodes, branches, failed branches/backtracks, and maximum depth.
- Unique generation with deterministic seeds and explicit `none`, `rot180`, and `mix` removal semantics.
- Strict single-clue minimality for `minimal=True` with `none`/`mix`; symmetry-preserving orbit-minimality for `minimal=True, symmetry="rot180"`.
- Row-major, valid, idempotent canonical representatives for supported Sudoku isomorphs.
- Deterministic difficulty v3 based on canonicalized search work rather than wall-clock timing.
- Independent optional SAT solving/CNF export.
- Fixed-corpus search-work regression checks plus property-based/nightly validation.

## Install for development

```bash
git clone https://github.com/SaridakisStamatisChristos/sudoku_dlx
cd sudoku_dlx
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
python -m pip install -e ".[dev]"
pytest -q
```

Optional SAT cross-check:

```bash
python -m pip install -e ".[sat]"
```

## Hello Sudoku

```python
from sudoku_dlx import from_string, solve, to_string

puzzle = from_string(
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)
result = solve(puzzle)
assert result is not None
print(to_string(result.grid))
print(result.stats)
```

## Documentation

- [Quickstart](quickstart.md)
- [CLI reference](cli.md)
- [Python API](api.md)
- [Human strategies](strategies.md)
- [Datasets & batch tooling](batch.md)
- [v1.0 hardening audit](V1_HARDENING.md)
- [Changelog highlights](changelog.md)
