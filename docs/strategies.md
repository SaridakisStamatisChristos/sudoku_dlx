# Human Strategies

Deterministic ordering, **one elimination per step** for stable playback:

## Placements
- **Naked single** — only one candidate in a cell
- **Hidden single** — the only place for a digit in a unit (row/col/box)

## Eliminations
- **Locked candidates**
  - Pointing (box → line)
  - Claiming (line → box)
- **Pairs**
  - Naked pair
  - Hidden pair
- **Triples**
  - Naked triple
  - Hidden triple
- **Fish**
  - X-Wing (rows/cols)
  - Swordfish (rows/cols)
- **Coloring**
  - Simple coloring (Rule 2)

These are implemented in `sudoku_dlx/strategies.py` and consumed by `explain()`.
