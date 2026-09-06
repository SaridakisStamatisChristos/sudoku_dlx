from __future__ import annotations

import random
from typing import Literal, Optional

from .api import Grid, count_solutions
from .solver import random_complete

Symmetry = Literal["none", "rot180", "mix"]
Cell = tuple[int, int]
RemovalGroup = tuple[Cell, ...]

_VALID_SYMMETRIES = {"none", "rot180", "mix"}


def _random_full_solution(seed: Optional[int]) -> Grid:
    """
    Produce a deterministic randomized complete grid.

    Completed grids are created directly from a valid Latin-pattern solution via
    Sudoku-preserving band/stack/row/column/digit permutations. This avoids the
    former sequence of repeated partial solves during generation.
    """

    return random_complete(rng=random.Random(seed))


def _rot180(r: int, c: int) -> Cell:
    return 8 - r, 8 - c


def _rot180_orbits() -> list[RemovalGroup]:
    seen: set[Cell] = set()
    groups: list[RemovalGroup] = []
    for r in range(9):
        for c in range(9):
            cell = (r, c)
            if cell in seen:
                continue
            mate = _rot180(r, c)
            seen.add(cell)
            seen.add(mate)
            groups.append((cell,) if cell == mate else (cell, mate))
    return groups


def _removal_schedule(symmetry: Symmetry, rng: random.Random) -> list[RemovalGroup]:
    cells = [(r, c) for r in range(9) for c in range(9)]

    if symmetry == "none":
        rng.shuffle(cells)
        return [(cell,) for cell in cells]

    orbits = _rot180_orbits()
    rng.shuffle(orbits)
    if symmetry == "rot180":
        return orbits

    # mix: prefer symmetric removals, then permit single-cell cleanup. This makes
    # the mode genuinely mixed rather than an alias for rot180.
    singles = cells[:]
    rng.shuffle(singles)
    return orbits + [(cell,) for cell in singles]


def _uniqueness(grid: Grid) -> bool:
    return count_solutions(grid, limit=2) == 1


def _remaining_clues(grid: Grid) -> int:
    return sum(1 for row in grid for value in row if value != 0)


def _try_remove_group(grid: Grid, group: RemovalGroup) -> bool:
    present = [(r, c, grid[r][c]) for r, c in group if grid[r][c] != 0]
    if not present:
        return False
    for r, c, _ in present:
        grid[r][c] = 0
    if _uniqueness(grid):
        return True
    for r, c, value in present:
        grid[r][c] = value
    return False


def _strict_minimal(grid: Grid) -> bool:
    if not _uniqueness(grid):
        return False
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                continue
            keep = grid[r][c]
            grid[r][c] = 0
            still_unique = _uniqueness(grid)
            grid[r][c] = keep
            if still_unique:
                return False
    return True


def _make_strict_minimal(grid: Grid) -> Grid:
    """Remove clues until every remaining individual clue is necessary."""

    changed = True
    while changed:
        changed = False
        # Dense units first is a deterministic, inexpensive removal heuristic.
        row_count = [sum(value != 0 for value in row) for row in grid]
        col_count = [sum(grid[r][c] != 0 for r in range(9)) for c in range(9)]
        clues = [(r, c) for r in range(9) for c in range(9) if grid[r][c] != 0]
        clues.sort(key=lambda rc: -(row_count[rc[0]] + col_count[rc[1]]))
        for r, c in clues:
            keep = grid[r][c]
            grid[r][c] = 0
            if _uniqueness(grid):
                changed = True
            else:
                grid[r][c] = keep

    assert _strict_minimal(grid)
    return grid


def _make_rot180_orbit_minimal(grid: Grid) -> Grid:
    """
    Preserve exact 180-degree clue-pattern symmetry while minimizing.

    Minimality here is with respect to symmetry orbits (paired clues, plus the
    center cell). Standard single-clue minimality and exact rotational symmetry
    are distinct constraints; silently breaking the requested symmetry would be
    worse than conflating the two definitions.
    """

    changed = True
    while changed:
        changed = False
        for group in _rot180_orbits():
            if _try_remove_group(grid, group):
                changed = True

    # Verify no complete rotational orbit can still be removed.
    for group in _rot180_orbits():
        present = [(r, c, grid[r][c]) for r, c in group if grid[r][c] != 0]
        if not present:
            continue
        for r, c, _ in present:
            grid[r][c] = 0
        still_unique = _uniqueness(grid)
        for r, c, value in present:
            grid[r][c] = value
        if still_unique:
            raise AssertionError("rot180 orbit-minimality invariant failed")
    return grid


def _is_rot180_pattern(grid: Grid) -> bool:
    for r in range(9):
        for c in range(9):
            if (grid[r][c] != 0) != (grid[8 - r][8 - c] != 0):
                return False
    return True


def generate(
    seed: Optional[int] = None,
    *,
    target_givens: int = 28,
    minimal: bool = False,
    symmetry: Symmetry = "mix",
) -> Grid:
    """
    Create a uniquely solvable Sudoku puzzle.

    ``target_givens`` is an approximate lower target: a removal is skipped if it
    would cross below the target.

    Symmetry modes:
      - ``none``: single-cell removals.
      - ``rot180``: exact 180-degree clue-pattern symmetry.
      - ``mix``: symmetric removals first, then single-cell cleanup.

    With ``minimal=True``, ``none`` and ``mix`` enforce standard strict
    single-clue minimality. ``rot180`` preserves exact symmetry and therefore
    uses orbit-minimality: no rotational clue orbit can be removed while
    retaining uniqueness.
    """

    if type(target_givens) is not int or not 17 <= target_givens <= 81:
        raise ValueError("target_givens must be an integer in 17..81")
    if symmetry not in _VALID_SYMMETRIES:
        raise ValueError("symmetry must be one of: none, rot180, mix")

    rng = random.Random(seed)
    puzzle = _random_full_solution(seed)
    schedule = _removal_schedule(symmetry, rng)

    for group in schedule:
        remaining = _remaining_clues(puzzle)
        if remaining <= target_givens:
            break
        removable = sum(puzzle[r][c] != 0 for r, c in group)
        if removable == 0 or remaining - removable < target_givens:
            continue
        _try_remove_group(puzzle, group)

    if minimal:
        if symmetry == "rot180":
            _make_rot180_orbit_minimal(puzzle)
        else:
            _make_strict_minimal(puzzle)

    if not _uniqueness(puzzle):
        raise AssertionError("generator produced a non-unique puzzle")
    if symmetry == "rot180" and not _is_rot180_pattern(puzzle):
        raise AssertionError("generator violated rot180 clue-pattern symmetry")
    return puzzle


__all__ = ["Symmetry", "generate"]
