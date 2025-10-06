from __future__ import annotations

"""Lightweight human strategies:
 - candidates() snapshot
 - naked_single
 - hidden_single (row/col/box)
 - locked candidates (pointing: box -> line)
 - box-line claiming (line -> box)
 - naked_pair (row/col/box)
 - hidden_pair (row/col/box)
 - naked_triple (row/col/box)
 - hidden_triple (row/col/box)
 - x_wing (rows/cols)
 - swordfish (rows/cols)
 - simple_coloring (Rule 2 style, one elimination)
Deterministic scan order for reproducible explanations.
"""

import itertools
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Cand = List[List[Set[int]]]


def _box_id(r: int, c: int) -> int:
    return (r // 3) * 3 + (c // 3)


def _unit_cells(kind: str, idx: int) -> List[Tuple[int, int]]:
    if kind == "row":
        return [(idx, c) for c in range(9)]
    if kind == "col":
        return [(r, idx) for r in range(9)]
    if kind == "box":
        br, bc = (idx // 3) * 3, (idx % 3) * 3
        return [(br + dr, bc + dc) for dr in range(3) for dc in range(3)]
    raise ValueError(f"unknown unit kind: {kind}")


def _unit_cells_row(r: int) -> List[Tuple[int, int]]:
    return _unit_cells("row", r)


def _unit_cells_col(c: int) -> List[Tuple[int, int]]:
    return _unit_cells("col", c)


def _unit_cells_box(b: int) -> List[Tuple[int, int]]:
    return _unit_cells("box", b)


def candidates(grid: Grid) -> Cand:
    """Compute candidate sets for each empty cell (deterministic)."""
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = grid[r][c]
            if v:
                rows[r].add(v)
                cols[c].add(v)
                boxes[_box_id(r, c)].add(v)
    out: Cand = [[set() for _ in range(9)] for _ in range(9)]
    allv = set(range(1, 10))
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                out[r][c] = allv - rows[r] - cols[c] - boxes[_box_id(r, c)]
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


def _hidden_single_in_unit(
    grid: Grid, cand: Cand, cells: List[Tuple[int, int]], unit_kind: str, unit_idx: int
) -> Optional[Dict]:
    # map digit -> cells where it can go
    places: Dict[int, List[Tuple[int, int]]] = {d: [] for d in range(1, 10)}
    for (r, c) in cells:
        if grid[r][c] != 0:
            continue
        for d in cand[r][c]:
            places[d].append((r, c))
    for d in range(1, 10):
        locs = places[d]
        if len(locs) == 1:
            r, c = locs[0]
            grid[r][c] = d
            return {
                "type": "place",
                "strategy": "hidden_single",
                "unit": unit_kind,
                "unit_index": unit_idx,
                "r": r,
                "c": c,
                "v": d,
            }
    return None


def apply_hidden_single(grid: Grid, cand: Cand) -> Optional[Dict]:
    # rows
    for r in range(9):
        move = _hidden_single_in_unit(grid, cand, _unit_cells("row", r), "row", r)
        if move:
            return move
    # cols
    for c in range(9):
        move = _hidden_single_in_unit(grid, cand, _unit_cells("col", c), "col", c)
        if move:
            return move
    # boxes
    for b in range(9):
        move = _hidden_single_in_unit(grid, cand, _unit_cells("box", b), "box", b)
        if move:
            return move
    return None


def apply_locked_candidates_pointing(grid: Grid, cand: Cand) -> Optional[Dict]:
    """Pointing: in a 3x3 box, if all candidates for digit d lie in the same row/col, eliminate outside."""
    for b in range(9):
        cells = _unit_cells("box", b)
        for d in range(1, 10):
            locs = [(r, c) for (r, c) in cells if grid[r][c] == 0 and d in cand[r][c]]
            if len(locs) < 2:
                continue
            rows = {r for (r, _) in locs}
            cols = {c for (_, c) in locs}
            if len(rows) == 1:
                r = next(iter(rows))
                for c in range(9):
                    if _box_id(r, c) == b:
                        continue
                    if grid[r][c] == 0 and d in cand[r][c]:
                        cand[r][c].remove(d)
                        return {
                            "type": "eliminate",
                            "strategy": "locked_pointing_row",
                            "box": b,
                            "r": r,
                            "c": c,
                            "v": d,
                        }
            if len(cols) == 1:
                c = next(iter(cols))
                for r in range(9):
                    if _box_id(r, c) == b:
                        continue
                    if grid[r][c] == 0 and d in cand[r][c]:
                        cand[r][c].remove(d)
                        return {
                            "type": "eliminate",
                            "strategy": "locked_pointing_col",
                            "box": b,
                            "r": r,
                            "c": c,
                            "v": d,
                        }
    return None


def apply_box_line_claiming(grid: Grid, cand: Cand) -> Optional[Dict]:
    """Claiming: if in a row/col all candidates for d lie in one box, eliminate d elsewhere in that box."""
    # rows -> box
    for r in range(9):
        cells = _unit_cells("row", r)
        for d in range(1, 10):
            locs = [(r, c) for (_, c) in cells if grid[r][c] == 0 and d in cand[r][c]]
            if len(locs) < 2:
                continue
            boxes = {_box_id(rr, cc) for (rr, cc) in locs}
            if len(boxes) == 1:
                box = boxes.pop()
                for (rr, cc) in _unit_cells("box", box):
                    if rr == r:
                        continue
                    if grid[rr][cc] == 0 and d in cand[rr][cc]:
                        cand[rr][cc].remove(d)
                        return {
                            "type": "eliminate",
                            "strategy": "box_line_row",
                            "box": box,
                            "unit": "row",
                            "unit_index": r,
                            "r": rr,
                            "c": cc,
                            "v": d,
                        }
    # cols -> box
    for c in range(9):
        cells = _unit_cells("col", c)
        for d in range(1, 10):
            locs = [(r, c) for (r, _) in cells if grid[r][c] == 0 and d in cand[r][c]]
            if len(locs) < 2:
                continue
            boxes = {_box_id(rr, cc) for (rr, cc) in locs}
            if len(boxes) == 1:
                box = boxes.pop()
                for (rr, cc) in _unit_cells("box", box):
                    if cc == c:
                        continue
                    if grid[rr][cc] == 0 and d in cand[rr][cc]:
                        cand[rr][cc].remove(d)
                        return {
                            "type": "eliminate",
                            "strategy": "box_line_col",
                            "box": box,
                            "unit": "col",
                            "unit_index": c,
                            "r": rr,
                            "c": cc,
                            "v": d,
                        }
    return None


def apply_naked_pair(grid: Grid, cand: Cand) -> Optional[Dict]:
    """Naked pair: if two cells share the same pair, remove from others in unit."""
    for kind in ("row", "col", "box"):
        for idx in range(9):
            cells = _unit_cells(kind, idx)
            seen: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
            for (r, c) in cells:
                if grid[r][c] != 0:
                    continue
                if len(cand[r][c]) == 2:
                    key = tuple(sorted(cand[r][c]))
                    seen.setdefault(key, []).append((r, c))
            for pair, locs in seen.items():
                if len(locs) == 2:
                    pair_set = set(pair)
                    for (r, c) in cells:
                        if (r, c) in locs or grid[r][c] != 0:
                            continue
                        inter = cand[r][c] & pair_set
                        if inter:
                            v = sorted(inter)[0]
                            cand[r][c].remove(v)
                            return {
                                "type": "eliminate",
                                "strategy": "naked_pair",
                                "unit": kind,
                                "unit_index": idx,
                                "r": r,
                                "c": c,
                                "remove": v,
                                "pair": list(pair),
                            }
    return None


def apply_hidden_pair(grid: Grid, cand: Cand) -> Optional[Dict]:
    """Hidden pair: if two digits only appear in the same two cells, eliminate other digits there."""
    for kind in ("row", "col", "box"):
        for idx in range(9):
            cells = _unit_cells(kind, idx)
            places: Dict[int, List[Tuple[int, int]]] = {d: [] for d in range(1, 10)}
            for (r, c) in cells:
                if grid[r][c] != 0:
                    continue
                for d in cand[r][c]:
                    places[d].append((r, c))
            digits = [d for d in range(1, 10) if 1 <= len(places[d]) <= 2]
            for a, b in itertools.combinations(digits, 2):
                locs = set(places[a]) | set(places[b])
                if len(locs) == 2 and places[a] and places[b]:
                    for (r, c) in locs:
                        extras = [x for x in cand[r][c] if x not in (a, b)]
                        if extras:
                            x = extras[0]
                            cand[r][c].remove(x)
                            return {
                                "type": "eliminate",
                                "strategy": "hidden_pair",
                                "unit": kind,
                                "unit_index": idx,
                                "r": r,
                                "c": c,
                                "remove": x,
                                "pair": [a, b],
                            }
    return None


def _triples(
    iterable: Sequence[Tuple[int, int]]
) -> Iterable[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
    return itertools.combinations(iterable, 3)


def apply_naked_triple(grid: Grid, cand: Cand) -> Optional[Dict]:
    """
    If three cells in a unit collectively contain exactly three digits (each cell ⊆ that set, sizes 2–3),
    eliminate those three digits from all other cells in the unit. One elimination per call.
    """
    for kind in ("row", "col", "box"):
        for idx in range(9):
            cells = _unit_cells(kind, idx)
            small = [
                (r, c)
                for (r, c) in cells
                if grid[r][c] == 0 and 1 < len(cand[r][c]) <= 3
            ]
            for (a, b, c) in _triples(small):
                r1, c1 = a
                r2, c2 = b
                r3, c3 = c
                union = cand[r1][c1] | cand[r2][c2] | cand[r3][c3]
                if 2 <= len(union) <= 3 and cand[r1][c1] <= union and cand[r2][c2] <= union and cand[r3][c3] <= union:
                    for (r, c) in cells:
                        if (r, c) in (a, b, c) or grid[r][c] != 0:
                            continue
                        inter = cand[r][c] & union
                        if inter:
                            v = sorted(inter)[0]
                            cand[r][c].remove(v)
                            return {
                                "type": "eliminate",
                                "strategy": "naked_triple",
                                "unit": kind,
                                "unit_index": idx,
                                "r": r,
                                "c": c,
                                "v": v,
                                "triple": sorted(union),
                            }
    return None


def apply_hidden_triple(grid: Grid, cand: Cand) -> Optional[Dict]:
    """
    If exactly three digits appear as candidates in exactly three cells of a unit,
    restrict those three cells' candidates to that set (drop any extras). One elimination per call.
    """
    for kind in ("row", "col", "box"):
        for idx in range(9):
            cells = _unit_cells(kind, idx)
            places: Dict[int, List[Tuple[int, int]]] = {d: [] for d in range(1, 10)}
            for (r, c) in cells:
                if grid[r][c] != 0:
                    continue
                for d in cand[r][c]:
                    places[d].append((r, c))
            digits = [d for d in range(1, 10) if 1 <= len(places[d]) <= 3]
            for a, b, c in itertools.combinations(digits, 3):
                triple = {a, b, c}
                locs = set(places[a]) | set(places[b]) | set(places[c])
                if len(locs) == 3:
                    for (r, c2) in locs:
                        extras = [x for x in cand[r][c2] if x not in triple]
                        if extras:
                            x = extras[0]
                            cand[r][c2].remove(x)
                            return {
                                "type": "eliminate",
                                "strategy": "hidden_triple",
                                "unit": kind,
                                "unit_index": idx,
                                "r": r,
                                "c": c2,
                                "remove": x,
                                "triple": sorted(triple),
                            }
    return None


def apply_x_wing(grid: Grid, cand: Cand) -> Optional[Dict]:
    """
    X-Wing (size-2 fish) on rows and columns.
    - Rows: if for a digit d, exactly two rows each have candidates only in the same two columns {c1,c2},
      eliminate d from those columns in all other rows.
    - Columns: symmetric.
    One elimination per call (first found in deterministic order).
    """
    for d in range(1, 10):
        row_cols: List[Tuple[int, Tuple[int, int]]] = []
        for r in range(9):
            cols = tuple(sorted([c for c in range(9) if grid[r][c] == 0 and d in cand[r][c]]))
            if len(cols) == 2:
                row_cols.append((r, (cols[0], cols[1])))
        by_pair: Dict[Tuple[int, int], List[int]] = {}
        for r, pair in row_cols:
            by_pair.setdefault(pair, []).append(r)
        for (c1, c2), rows2 in by_pair.items():
            if len(rows2) == 2:
                r1, r2 = rows2
                for rr in range(9):
                    if rr in (r1, r2):
                        continue
                    for cc in (c1, c2):
                        if grid[rr][cc] == 0 and d in cand[rr][cc]:
                            cand[rr][cc].remove(d)
                            return {
                                "type": "eliminate",
                                "strategy": "x_wing_row",
                                "digit": d,
                                "rows": [r1, r2],
                                "cols": [c1, c2],
                                "r": rr,
                                "c": cc,
                            }
    for d in range(1, 10):
        col_rows: List[Tuple[int, Tuple[int, int]]] = []
        for c in range(9):
            rows = tuple(sorted([r for r in range(9) if grid[r][c] == 0 and d in cand[r][c]]))
            if len(rows) == 2:
                col_rows.append((c, (rows[0], rows[1])))
        by_pair: Dict[Tuple[int, int], List[int]] = {}
        for c, pair in col_rows:
            by_pair.setdefault(pair, []).append(c)
        for (r1, r2), cols2 in by_pair.items():
            if len(cols2) == 2:
                c1, c2 = cols2
                for cc in range(9):
                    if cc in (c1, c2):
                        continue
                    for rr in (r1, r2):
                        if grid[rr][cc] == 0 and d in cand[rr][cc]:
                            cand[rr][cc].remove(d)
                            return {
                                "type": "eliminate",
                                "strategy": "x_wing_col",
                                "digit": d,
                                "rows": [r1, r2],
                                "cols": [c1, c2],
                                "r": rr,
                                "c": cc,
                            }
    return None


def apply_swordfish(grid: Grid, cand: Cand) -> Optional[Dict]:
    """
    Swordfish (size-3 fish) on rows and columns.
    Rows: for digit d, find three rows where d appears only in the same three columns {c1,c2,c3};
          eliminate d from those columns in all other rows. Columns follow symmetrically.
    Returns after the first deterministic elimination.
    """

    for d in range(1, 10):
        row_cols: List[Tuple[int, Tuple[int, ...]]] = []
        for r in range(9):
            cols = tuple(sorted(c for c in range(9) if grid[r][c] == 0 and d in cand[r][c]))
            if 2 <= len(cols) <= 3:
                row_cols.append((r, cols))
        for (r1, cset1), (r2, cset2), (r3, cset3) in itertools.combinations(row_cols, 3):
            cols_union = sorted(set(cset1) | set(cset2) | set(cset3))
            if len(cols_union) != 3:
                continue
            for rr in range(9):
                if rr in (r1, r2, r3):
                    continue
                for cc in cols_union:
                    if grid[rr][cc] == 0 and d in cand[rr][cc]:
                        cand[rr][cc].remove(d)
                        return {
                            "type": "eliminate",
                            "strategy": "swordfish_row",
                            "digit": d,
                            "rows": [r1, r2, r3],
                            "cols": cols_union,
                            "r": rr,
                            "c": cc,
                        }
    for d in range(1, 10):
        col_rows: List[Tuple[int, Tuple[int, ...]]] = []
        for c in range(9):
            rows = tuple(sorted(r for r in range(9) if grid[r][c] == 0 and d in cand[r][c]))
            if 2 <= len(rows) <= 3:
                col_rows.append((c, rows))
        for (c1, rset1), (c2, rset2), (c3, rset3) in itertools.combinations(col_rows, 3):
            rows_union = sorted(set(rset1) | set(rset2) | set(rset3))
            if len(rows_union) != 3:
                continue
            for cc in range(9):
                if cc in (c1, c2, c3):
                    continue
                for rr in rows_union:
                    if grid[rr][cc] == 0 and d in cand[rr][cc]:
                        cand[rr][cc].remove(d)
                        return {
                            "type": "eliminate",
                            "strategy": "swordfish_col",
                            "digit": d,
                            "rows": rows_union,
                            "cols": [c1, c2, c3],
                            "r": rr,
                            "c": cc,
                        }
    return None


def apply_simple_coloring(grid: Grid, cand: Cand) -> Optional[Dict]:
    """
    Simple coloring (Rule 2) on conjugate links for each digit d:
      - Build graph where nodes are candidate cells, edges connect two cells in a unit that contains
        exactly two candidates for d (conjugate link).
      - Two-color each connected component. If a color appears twice in the same unit, that color is
        impossible there; eliminate the first deterministic cell.
    Returns one elimination per call.
    """

    for d in range(1, 10):
        nodes = [(r, c) for r in range(9) for c in range(9) if grid[r][c] == 0 and d in cand[r][c]]
        if not nodes:
            continue
        idx = {rc: i for i, rc in enumerate(nodes)}
        adj: List[List[int]] = [[] for _ in nodes]

        def add_links(cells: List[Tuple[int, int]]) -> None:
            locs = [(r, c) for (r, c) in cells if grid[r][c] == 0 and d in cand[r][c]]
            if len(locs) == 2:
                a, b = idx[locs[0]], idx[locs[1]]
                adj[a].append(b)
                adj[b].append(a)

        for r in range(9):
            add_links(_unit_cells_row(r))
        for c in range(9):
            add_links(_unit_cells_col(c))
        for b in range(9):
            add_links(_unit_cells_box(b))

        color: List[Optional[int]] = [None] * len(nodes)
        for start in range(len(nodes)):
            if color[start] is not None:
                continue
            color[start] = 0
            stack = [start]
            while stack:
                u = stack.pop()
                for v in adj[u]:
                    if color[v] is None:
                        color[v] = 1 - color[u]
                        stack.append(v)

        for unit_kind in ("row", "col", "box"):
            for unit_idx in range(9):
                cells = [
                    (r, c)
                    for (r, c) in _unit_cells(unit_kind, unit_idx)
                    if grid[r][c] == 0 and d in cand[r][c] and (r, c) in idx
                ]
                if len(cells) < 2:
                    continue
                by_color: Dict[int, List[Tuple[int, int]]] = {}
                for (r, c) in cells:
                    col = color[idx[(r, c)]]
                    if col is None:
                        continue
                    by_color.setdefault(col, []).append((r, c))
                for col_value, positions in sorted(by_color.items()):
                    if len(positions) >= 2:
                        r, c = positions[0]
                        if d in cand[r][c]:
                            cand[r][c].remove(d)
                            return {
                                "type": "eliminate",
                                "strategy": "simple_coloring",
                                "digit": d,
                                "unit": unit_kind,
                                "unit_index": unit_idx,
                                "color": col_value,
                                "r": r,
                                "c": c,
                            }
    return None


def step_once(grid: Grid) -> Optional[Dict]:
    """
    Apply exactly one logical step (prioritized order). Returns a move dict or None.
    Priority:
      1) Placements: naked_single > hidden_single
      2) Eliminations: locked_pointing > box_line_claiming > naked_pair > hidden_pair
                        > x_wing > naked_triple > hidden_triple > swordfish > simple_coloring
    """
    cand = candidates(grid)
    m = apply_naked_single(grid, cand)
    if m:
        return m
    m = apply_hidden_single(grid, cand)
    if m:
        return m
    m = apply_locked_candidates_pointing(grid, cand)
    if m:
        return m
    m = apply_box_line_claiming(grid, cand)
    if m:
        return m
    m = apply_naked_pair(grid, cand)
    if m:
        return m
    m = apply_hidden_pair(grid, cand)
    if m:
        return m
    m = apply_x_wing(grid, cand)
    if m:
        return m
    m = apply_naked_triple(grid, cand)
    if m:
        return m
    m = apply_hidden_triple(grid, cand)
    if m:
        return m
    m = apply_swordfish(grid, cand)
    if m:
        return m
    m = apply_simple_coloring(grid, cand)
    return m


__all__ = [
    "candidates",
    "apply_naked_single",
    "apply_hidden_single",
    "apply_locked_candidates_pointing",
    "apply_box_line_claiming",
    "apply_naked_pair",
    "apply_hidden_pair",
    "apply_naked_triple",
    "apply_hidden_triple",
    "apply_x_wing",
    "apply_swordfish",
    "apply_simple_coloring",
    "step_once",
]
