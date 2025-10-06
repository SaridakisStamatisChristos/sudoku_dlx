# Sudoku DLX

Fast **Sudoku** solver & generator using **Algorithm X / Dancing Links** with **Python bitsets**.  
Includes **unique/minimal** generation, **difficulty v2**, **canonicalization**, **explainable steps**, batch tools, and a JS demo.

**Repo:** [:octicons-mark-github-16: GitHub](https://github.com/SaridakisStamatisChristos/sudoku_dlx) · **Docs:** this site · **Demo:** GitHub Pages `web/` and `visualizer.html`.

## Features
- Bitset DLX solver with stats (nodes, backtracks)
- Unique/minimal generator with symmetry controls
- Deterministic **difficulty v2** ([0,10])
- Canonical form & dataset de-duplication
- Human strategies: singles, pairs, triples, **X-Wing**, **Swordfish**, **Simple Coloring**
- CLI for solve/rate/gen/canon/explain/batch

## Install
```bash
python -m pip install sudoku_dlx  # (after PyPI publish)
```
For development:
```bash
git clone https://github.com/SaridakisStamatisChristos/sudoku_dlx
cd sudoku_dlx
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```
Optional SAT cross-check:
```bash
pip install -e ".[sat]"
```

## Hello Sudoku
```python
from sudoku_dlx import from_string, solve, to_string, explain
g = from_string("53..7....6..195... ...")  # 81 chars; dots for blanks
res = solve(g)
print(to_string(res.grid))
steps = explain(g, max_steps=200)
print(steps["steps"][:3])  # preview moves
```

## Links
- CLI Guide: [CLI reference](cli.md)
- API Reference: [Python API](api.md)
- Strategies: [Human strategies](strategies.md)
- Batch: [Datasets & tooling](batch.md)
