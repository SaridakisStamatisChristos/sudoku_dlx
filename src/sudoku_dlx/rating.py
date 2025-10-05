from __future__ import annotations

import math
from itertools import permutations, product
from .api import Grid, solve, to_string, is_valid, from_string
from .canonical import canonical_form


def _clone(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def _rot90(g: Grid) -> Grid:
    return [[g[9 - 1 - c][r] for c in range(9)] for r in range(9)]


def _rot180(g: Grid) -> Grid:
    return [[g[9 - 1 - r][9 - 1 - c] for c in range(9)] for r in range(9)]


def _rot270(g: Grid) -> Grid:
    return [[g[c][9 - 1 - r] for c in range(9)] for r in range(9)]


def _flip_h(g: Grid) -> Grid:
    return [[g[r][9 - 1 - c] for c in range(9)] for r in range(9)]


def _flip_v(g: Grid) -> Grid:
    return [g[9 - 1 - r][:] for r in range(9)]


def _flip_main(g: Grid) -> Grid:
    return [[g[c][r] for c in range(9)] for r in range(9)]


def _flip_anti(g: Grid) -> Grid:
    return [[g[9 - 1 - c][9 - 1 - r] for c in range(9)] for r in range(9)]


_D4_TRANSFORMS = (
    _clone,
    _rot90,
    _rot180,
    _rot270,
    _flip_h,
    _flip_v,
    _flip_main,
    _flip_anti,
)

_PERM3 = list(permutations((0, 1, 2)))

_RATING_CACHE: dict[str, float] = {}


def _canonical_signature(grid: Grid) -> str:
    """Stable key despite canonical_form cycling on unsolved puzzles."""
    current = canonical_form(grid)
    best = current
    seen: set[str] = set()
    while current not in seen:
        seen.add(current)
        if current < best:
            best = current
        current = canonical_form(from_string(current))
    if current < best:
        best = current
    return best


def _permute_bands(grid: Grid, band_perm: tuple[int, int, int]) -> Grid:
    return [grid[band * 3 + r][:] for band in band_perm for r in range(3)]


def _permute_rows_within_bands(grid: Grid, row_perms: tuple[tuple[int, int, int], ...]) -> Grid:
    rows: Grid = []
    for band_idx, row_perm in enumerate(row_perms):
        base = band_idx * 3
        for offset in row_perm:
            rows.append(grid[base + offset][:])
    return rows


def _assemble_stacks(grid: Grid) -> Grid | None:
    """Given a grid with chosen rows, pick stacks/columns yielding a valid grid."""
    result = [[0] * 9 for _ in range(9)]
    col_sets = [set() for _ in range(9)]
    box_sets = [[set() for _ in range(3)] for _ in range(3)]  # bands × stacks

    def backtrack(pos: int, used_mask: int) -> Grid | None:
        if pos == 3:
            return [row[:] for row in result]
        col_offset = pos * 3
        for stack in range(3):
            if used_mask & (1 << stack):
                continue
            for col_perm in _PERM3:
                ok = True
                added_cols = [list() for _ in range(3)]
                added_boxes = [list() for _ in range(3)]
                for r in range(9):
                    band = r // 3
                    for idx, offset in enumerate(col_perm):
                        val = grid[r][stack * 3 + offset]
                        c = col_offset + idx
                        result[r][c] = val
                        if val == 0:
                            continue
                        if val in col_sets[c] or val in box_sets[band][pos]:
                            ok = False
                            break
                        col_sets[c].add(val)
                        box_sets[band][pos].add(val)
                        added_cols[idx].append(val)
                        added_boxes[band].append(val)
                    if not ok:
                        break
                if ok:
                    res = backtrack(pos + 1, used_mask | (1 << stack))
                    if res is not None:
                        return res
                # rollback
                for r in range(9):
                    for idx in range(3):
                        result[r][col_offset + idx] = 0
                for idx, values in enumerate(added_cols):
                    c = col_offset + idx
                    for val in values:
                        col_sets[c].remove(val)
                for band in range(3):
                    for val in added_boxes[band]:
                        box_sets[band][pos].remove(val)
        return None

    return backtrack(0, 0)


def _find_valid_isomorph(grid: Grid) -> Grid | None:
    for tf in _D4_TRANSFORMS:
        g_tf = tf(grid)
        for band_perm in _PERM3:
            g_band = _permute_bands(g_tf, band_perm)
            for row_perms in product(_PERM3, repeat=3):
                g_rows = _permute_rows_within_bands(g_band, row_perms)
                iso = _assemble_stacks(g_rows)
                if iso is not None and is_valid(iso):
                    return iso
    return None


def rate(grid: Grid) -> float:
    """
    Difficulty v2 (deterministic, invariant under isomorphisms), range [0,10].
    Features:
      - f_gaps:    Empties proportion (81 - givens)
      - f_nodes:   log-scaled node count from the DLX search
      - f_bt:      log-scaled backtracks
      - f_fill:    Fill pressure: ratio of solved digits to original blanks

    Notes:
      - We avoid timing-based features (ms) for stability across machines.
      - If unsolvable, return 10.0.
    """
    # Copy grid for safety; compute givens/empties
    g = _clone(grid)
    signature = _canonical_signature(g)
    cached = _RATING_CACHE.get(signature)
    if cached is not None:
        return cached
    givens = sum(1 for r in range(9) for c in range(9) if g[r][c] != 0)
    empties = 81 - givens

    res = solve(_clone(g))
    if res is None:
        if not is_valid(g):
            iso = _find_valid_isomorph(g)
            if iso is None:
                return 10.0
            res = solve(_clone(iso))
            if res is None:
                return 10.0
            g = iso
        else:
            return 10.0

    # Nodes/backtracks with soft logs to reduce variance, emphasize early growth
    # Scale denominators chosen so that common values map to ~[0.2..0.8]
    def _log01(x: int, k: int) -> float:
        # normalized log in [0, ~1.2] for practical ranges
        return math.log1p(max(0, x)) / math.log1p(k)

    f_gaps  = min(empties / 60.0, 1.2)                             # 0..~1.2
    f_nodes = min(_log01(res.stats.nodes, 50000), 1.2)             # 0..~1.2
    f_bt    = min(_log01(res.stats.backtracks, 5000), 1.2)         # 0..~1.2

    # Fill pressure: how many cells solver filled relative to blanks
    solved_str = to_string(res.grid)
    filled = sum(1 for ch in solved_str if ch != ".") - givens     # number of cells actually filled
    f_fill = min((filled / max(1, empties)), 1.2)                   # 0..1.2

    # Blend with weights; keep sum <= 1.0 then scale to [0,10]
    # Emphasize nodes/backtracks; gaps/fill are supporting signals.
    score01 = (
        0.25 * f_gaps +
        0.40 * f_nodes +
        0.20 * f_bt +
        0.15 * f_fill
    )
    score = 10.0 * min(score01, 1.0)
    # Round to one decimal for presentation
    rounded = round(score, 1)
    _RATING_CACHE[signature] = rounded
    return rounded


__all__ = ["rate"]
