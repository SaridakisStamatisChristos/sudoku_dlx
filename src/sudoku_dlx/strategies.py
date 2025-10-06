from __future__ import annotations
"""
Lightweight human strategies:
 - candidates() snapshot
 - naked_single
 - hidden_single (row/col/box)
 - locked candidates (pointing)
Deterministic scan order for reproducible explanations.
"""
from typing import List, Dict, Set, Tuple, Optional

Grid = List[List[int]]
Cand = List[List[Set[int]]]

def _box_id(r: int, c: int) -> int:
    return (r // 3) * 3 + (c // 3)

def _unit_cells_row(r: int) -> List[Tuple[int,int]]:
    return [(r, c) for c in range(9)]

def _unit_cells_col(c: int) -> List[Tuple[int,int]]:
    return [(r, c) for r in range(9)]

def _unit_cells_box(b: int) -> List[Tuple[int,int]]:
    br, bc = (b // 3) * 3, (b % 3) * 3
    return [(br + dr, bc + dc) for dr in range(3) for dc in range(3)]

def candidates(grid: Grid) -> Cand:
    """Compute candidate sets for each empty cell (deterministic)."""
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = grid[r][c]
            if v:
                rows[r].add(v); cols[c].add(v); boxes[_box_id(r,c)].add(v)
    out: Cand = [[set() for _ in range(9)] for _ in range(9)]
    allv = set(range(1,10))
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                out[r][c] = allv - rows[r] - cols[c] - boxes[_box_id(r,c)]
    return out

# ----- Moves ------------------------------------------------------------------------------------

def apply_naked_single(grid: Grid, cand: Cand) -> Optional[Dict]:
    """If any cell has exactly one candidate, place it."""
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0 and len(cand[r][c]) == 1:
                v = next(iter(cand[r][c]))
                grid[r][c] = v
                return {"type": "place", "strategy": "naked_single", "r": r, "c": c, "v": v}
    return None

def _hidden_single_in_unit(grid: Grid, cand: Cand, cells: List[Tuple[int,int]], unit_kind: str, unit_idx: int) -> Optional[Dict]:
    # map digit -> cells where it can go
    places: Dict[int, List[Tuple[int,int]]] = {d: [] for d in range(1,10)}
    for (r,c) in cells:
        if grid[r][c] != 0:
            continue
        for d in cand[r][c]:
            places[d].append((r,c))
    for d in range(1,10):
        locs = places[d]
        if len(locs) == 1:
            r, c = locs[0]
            grid[r][c] = d
            return {"type": "place", "strategy": "hidden_single", "unit": unit_kind, "unit_index": unit_idx, "r": r, "c": c, "v": d}
    return None

def apply_hidden_single(grid: Grid, cand: Cand) -> Optional[Dict]:
    # rows
    for r in range(9):
        move = _hidden_single_in_unit(grid, cand, _unit_cells_row(r), "row", r)
        if move: return move
    # cols
    for c in range(9):
        move = _hidden_single_in_unit(grid, cand, _unit_cells_col(c), "col", c)
        if move: return move
    # boxes
    for b in range(9):
        move = _hidden_single_in_unit(grid, cand, _unit_cells_box(b), "box", b)
        if move: return move
    return None

def apply_locked_candidates_pointing(grid: Grid, cand: Cand) -> Optional[Dict]:
    """
    Pointing: in a 3x3 box, if all candidates for digit d lie in the same row (or same col),
    eliminate d from that row (or col) outside the box.
    Produces one elimination at a time for deterministic playback.
    """
    # For each box and digit, gather positions
    for b in range(9):
        cells = _unit_cells_box(b)
        for d in range(1,10):
            locs = [(r,c) for (r,c) in cells if grid[r][c] == 0 and d in cand[r][c]]
            if len(locs) < 2:
                continue
            rows = {r for (r,_) in locs}
            cols = {c for (_,c) in locs}
            if len(rows) == 1:
                r = next(iter(rows))
                # eliminate from row r, columns not in this box
                box_cols = {c for (_,c) in cells}
                for c in range(9):
                    if (r,c) not in locs and c not in box_cols and grid[r][c] == 0 and d in cand[r][c]:
                        cand[r][c].remove(d)
                        return {"type": "eliminate", "strategy": "locked_pointing_row", "box": b, "r": r, "c": c, "v": d}
            if len(cols) == 1:
                c = next(iter(cols))
                box_rows = {r for (r,_) in cells}
                for r in range(9):
                    if (r,c) not in locs and r not in box_rows and grid[r][c] == 0 and d in cand[r][c]:
                        cand[r][c].remove(d)
                        return {"type": "eliminate", "strategy": "locked_pointing_col", "box": b, "r": r, "c": c, "v": d}
    return None

def step_once(grid: Grid) -> Optional[Dict]:
    """
    Apply exactly one logical step (prioritized order). Returns a move dict or None.
    Priority: naked_single > hidden_single > locked_pointing (elimination)
    """
    cand = candidates(grid)
    m = apply_naked_single(grid, cand)
    if m: return m
    m = apply_hidden_single(grid, cand)
    if m: return m
    m = apply_locked_candidates_pointing(grid, cand)
    return m

__all__ = [
    "candidates",
    "apply_naked_single",
    "apply_hidden_single",
    "apply_locked_candidates_pointing",
    "step_once",
]
