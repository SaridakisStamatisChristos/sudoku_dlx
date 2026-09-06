from __future__ import annotations

"""
Canonical representatives for Sudoku puzzle isomorphism classes.

The search covers the standard structure-preserving transformations used here:
D4 board symmetries, band/stack permutations, row permutations within bands,
column permutations within stacks, and digit relabeling.

The search key is serialized in block-major order because that supports strong
prefix pruning. The public result is converted back to ordinary row-major
Sudoku order before it is returned. This distinction is important: older
versions returned the internal block-major key directly, so parsing the
"canonical" string as a normal grid could change the puzzle and make repeated
canonicalization cycle.
"""

from itertools import permutations
from typing import List, Sequence, Tuple

from .api import Grid, is_well_formed


def _rot90(g: Grid) -> Grid:
    return [[g[8 - c][r] for c in range(9)] for r in range(9)]


def _rot180(g: Grid) -> Grid:
    return [[g[8 - r][8 - c] for c in range(9)] for r in range(9)]


def _rot270(g: Grid) -> Grid:
    return [[g[c][8 - r] for c in range(9)] for r in range(9)]


def _flip_h(g: Grid) -> Grid:
    return [[g[r][8 - c] for c in range(9)] for r in range(9)]


def _flip_v(g: Grid) -> Grid:
    return [g[8 - r][:] for r in range(9)]


def _flip_main_diag(g: Grid) -> Grid:
    return [[g[c][r] for c in range(9)] for r in range(9)]


def _flip_anti_diag(g: Grid) -> Grid:
    return [[g[8 - c][8 - r] for c in range(9)] for r in range(9)]


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

_PERM3 = list(permutations((0, 1, 2)))


def _cell_char(value: int) -> str:
    return "." if value == 0 else str(value)


def _block_major_to_row_major(chars: Sequence[str]) -> str:
    """Convert the 9 contiguous 3x3 blocks used by the search to row-major order."""

    if len(chars) != 81:
        raise ValueError("canonical candidate must contain exactly 81 cells")
    out = [""] * 81
    for block_row in range(3):
        for block_col in range(3):
            block_start = (block_row * 3 + block_col) * 9
            for local_row in range(3):
                for local_col in range(3):
                    src = block_start + local_row * 3 + local_col
                    dst = (block_row * 3 + local_row) * 9 + block_col * 3 + local_col
                    out[dst] = chars[src]
    return "".join(out)


def _canonical_band_stack(
    grid_chars: Sequence[Sequence[str]],
    band_perm: Tuple[int, int, int],
    stack_perm: Tuple[int, int, int],
    best_key: str | None,
    best_repr: str | None,
) -> tuple[str | None, str | None]:
    """
    Search inner row/column permutations for one band/stack ordering.

    ``best_key`` is block-major and exists only to make lexicographic prefix
    pruning cheap. ``best_repr`` is the corresponding normal row-major grid.
    """

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
        nonlocal best_key, best_repr, next_digit, cmp_state

        if block_idx == 9:
            key = "".join(out_chars)
            if best_key is None or key < best_key:
                best_key = key
                best_repr = _block_major_to_row_major(key)
            return

        band_idx = block_idx // 3
        stack_idx = block_idx % 3
        band = band_perm[band_idx]
        stack = stack_perm[stack_idx]

        row_options = (chosen_row_perms[band],) if band in chosen_row_perms else _PERM3
        col_options = (chosen_col_perms[stack],) if stack in chosen_col_perms else _PERM3

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

                for local_row in row_perm:
                    row = grid_chars[band * 3 + local_row]
                    for local_col in col_perm:
                        ch = row[stack * 3 + local_col]
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
                        if best_key is not None and cmp_state == 0:
                            best_char = best_key[len(out_chars) - 1]
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

            if assigned_row:
                chosen_row_perms.pop(band, None)

    dfs(0)
    return best_key, best_repr


def canonical_form(grid: Grid) -> str:
    """
    Return a stable row-major representative for the puzzle's isomorphism class.

    The theoretical transformation space is 8 × (3!)^8. Prefix pruning avoids
    materializing that space in normal use. Digit labels are normalized by first
    appearance in the internal canonical search order.
    """

    if not is_well_formed(grid):
        raise ValueError("grid must be a 9x9 list of integers in 0..9")

    best_key: str | None = None
    best_repr: str | None = None

    for transform in _TRANSFORMS:
        transformed = transform(grid)
        grid_chars = [[_cell_char(cell) for cell in row] for row in transformed]
        for band_perm in _PERM3:
            for stack_perm in _PERM3:
                best_key, best_repr = _canonical_band_stack(
                    grid_chars,
                    band_perm,
                    stack_perm,
                    best_key,
                    best_repr,
                )

    assert best_repr is not None
    return best_repr


__all__ = ["canonical_form"]
