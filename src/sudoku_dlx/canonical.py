from __future__ import annotations
"""
State-of-the-art canonicalization for Sudoku puzzles.

Maps isomorphic puzzles to a single 81-char canonical form using:
  • Dihedral symmetries D4 (8 transforms)
  • Band (row bands) and stack (column stacks) permutations (3! each)
  • Row swaps within each band and column swaps within each stack (3! for each band/stack)
  • Greedy digit relabeling (first-appearance maps to 1..9)

Total variants explored per grid: 8 × (3!)^4 = 10,368 — acceptable for CLI/tests.
"""
from itertools import permutations
from typing import List, Sequence, Tuple

from .api import Grid

# --------- Dihedral transforms over 9x9 grids (D4) ----------

def _rot90(g: Grid) -> Grid:
    return [[g[9 - 1 - c][r] for c in range(9)] for r in range(9)]


def _rot180(g: Grid) -> Grid:
    return [[g[9 - 1 - r][9 - 1 - c] for c in range(9)] for r in range(9)]


def _rot270(g: Grid) -> Grid:
    return [[g[c][9 - 1 - r] for c in range(9)] for r in range(9)]


def _flip_h(g: Grid) -> Grid:
    # horizontal flip (mirror over vertical axis)
    return [[g[r][9 - 1 - c] for c in range(9)] for r in range(9)]


def _flip_v(g: Grid) -> Grid:
    # vertical flip (mirror over horizontal axis)
    return [g[9 - 1 - r][:] for r in range(9)]


def _flip_main_diag(g: Grid) -> Grid:
    # transpose over main diagonal
    return [[g[c][r] for c in range(9)] for r in range(9)]


def _flip_anti_diag(g: Grid) -> Grid:
    # reflect over anti-diagonal (r,c) -> (8-c,8-r)
    return [[g[9 - 1 - c][9 - 1 - r] for c in range(9)] for r in range(9)]


_TRANSFORMS = (
    lambda x: x,
    _rot90,
    _rot180,
    _rot270,
    _flip_h,
    _flip_v,
    _flip_main_diag,
    _flip_anti_diag,
)

# --------- Permutations for bands/stacks and inner rows/cols ----------

_PERM3 = list(permutations((0, 1, 2)))  # 6 perms


def _cell_char(value: int) -> str:
    if value == 0:
        return "."
    if isinstance(value, str):
        return value if value not in {"0", "-"} else "."
    return str(value)


def _canonical_band_stack(
    grid_chars: Sequence[Sequence[str]],
    band_perm: Tuple[int, int, int],
    stack_perm: Tuple[int, int, int],
    best: str | None,
) -> str | None:
    best_local = best
    chosen_row_perms: dict[int, Tuple[int, int, int]] = {}
    chosen_col_perms: dict[int, Tuple[int, int, int]] = {}
    mapping: dict[str, str] = {}
    out_chars: List[str] = []
    next_digit = ord("1")
    cmp_state = 0

    def rollback(inserted: List[str], saved_len: int, saved_next: int, saved_cmp: int) -> None:
        nonlocal next_digit, cmp_state
        del out_chars[saved_len:]
        next_digit = saved_next
        cmp_state = saved_cmp
        for key in reversed(inserted):
            mapping.pop(key, None)

    def dfs(block_idx: int) -> None:
        nonlocal best_local, next_digit, cmp_state
        if block_idx == 9:
            candidate = "".join(out_chars)
            if best_local is None or candidate < best_local:
                best_local = candidate
            return

        band_idx = block_idx // 3
        stack_idx = block_idx % 3
        band = band_perm[band_idx]
        stack = stack_perm[stack_idx]

        row_options = (
            (chosen_row_perms[band],)
            if band in chosen_row_perms
            else _PERM3
        )
        col_options = (
            (chosen_col_perms[stack],)
            if stack in chosen_col_perms
            else _PERM3
        )

        for row_perm in row_options:
            assigned_row = False
            if band not in chosen_row_perms:
                chosen_row_perms[band] = row_perm
                assigned_row = True
            for col_perm in col_options:
                assigned_col = False
                if stack not in chosen_col_perms:
                    chosen_col_perms[stack] = col_perm
                    assigned_col = True

                saved_len = len(out_chars)
                saved_next = next_digit
                saved_cmp = cmp_state
                inserted: List[str] = []
                pruned = False

                for r_local in row_perm:
                    row = grid_chars[band * 3 + r_local]
                    for c_local in col_perm:
                        ch = row[stack * 3 + c_local]
                        if ch == ".":
                            mapped = "."
                        else:
                            mapped = mapping.get(ch)
                            if mapped is None:
                                mapped = chr(next_digit)
                                mapping[ch] = mapped
                                inserted.append(ch)
                                if next_digit < ord("9"):
                                    next_digit += 1
                        out_chars.append(mapped)
                        if best_local is not None and cmp_state == 0:
                            best_char = best_local[len(out_chars) - 1]
                            if mapped > best_char:
                                pruned = True
                                break
                            if mapped < best_char:
                                cmp_state = -1
                    if pruned:
                        break

                if not pruned:
                    dfs(block_idx + 1)

                rollback(inserted, saved_len, saved_next, saved_cmp)

                if assigned_col:
                    chosen_col_perms.pop(stack, None)

                if pruned and best_local is not None and cmp_state == 0:
                    # If pruning occurred due to mapped > best prefix, remaining column perms
                    # in this branch are unlikely to improve; continue to next col perm.
                    pass

            if assigned_row:
                chosen_row_perms.pop(band, None)

    dfs(0)
    return best_local


# --------- Public API (full canon) ----------


def canonical_form(grid: Grid) -> str:
    """
    Return the lexicographically smallest normalized string among all:
      - D4 dihedral transforms
      - Band and stack permutations
      - Row swaps within each band, column swaps within each stack
    Each candidate is normalized by greedy digit relabeling before compare.
    """
    best: str | None = None
    for tf in _TRANSFORMS:
        g1 = tf(grid)
        grid_chars = [[_cell_char(cell) for cell in row] for row in g1]
        for band_perm in _PERM3:
            for stack_perm in _PERM3:
                cand = _canonical_band_stack(grid_chars, band_perm, stack_perm, best)
                if cand is not None and (best is None or cand < best):
                    best = cand
    assert best is not None
    return best


__all__ = ["canonical_form"]
