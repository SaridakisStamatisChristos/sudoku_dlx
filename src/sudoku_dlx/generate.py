from __future__ import annotations

import random
from typing import Optional, Union

from .api import Grid, count_solutions, is_valid, solve

Symmetry = str  # "none" | "rot180" | "mix"


def _empty_grid() -> Grid:
    return [[0] * 9 for _ in range(9)]


def _random_full_solution(seed: Optional[int]) -> Grid:
    """Produce a full valid solution by solving an empty grid with a randomized search order."""
    rng = random.Random(seed)
    grid = _empty_grid()
    attempts = 0
    while attempts < 30:
        r = rng.randrange(9)
        c = rng.randrange(9)
        if grid[r][c] != 0:
            attempts += 1
            continue
        values = list(range(1, 10))
        rng.shuffle(values)
        placed = False
        for value in values:
            grid[r][c] = value
            if is_valid(grid) and solve(grid) is not None:
                placed = True
                break
            grid[r][c] = 0
        if not placed:
            grid[r][c] = 0
        attempts += 1
    result = solve(grid)
    if result is None:
        raise RuntimeError("Failed to construct a full solution")
    return result.grid


def _rot180(r: int, c: int) -> tuple[int, int]:
    return 8 - r, 8 - c


PairOrCell = Union[tuple[int, int], tuple[tuple[int, int], tuple[int, int]]]


def _removal_schedule(symmetry: Symmetry, rng: random.Random) -> list[PairOrCell]:
    """
    Return a shuffled list of single cells or symmetric pairs to try
    removing, preserving adjacency for paired removals.
    """

    cells = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(cells)
    if symmetry == "none":
        return cells  # singles only

    # rot180 or mix → group into pairs; center maps to itself
    seen: set[tuple[int,int]] = set()
    pairs: list[PairOrCell] = []
    for (r, c) in cells:
        if (r, c) in seen:
            continue
        rr, cc = _rot180(r, c)
        seen.add((r, c))
        seen.add((rr, cc))
        if (r, c) == (rr, cc):
            pairs.append((r, c))
        else:
            pairs.append(((r, c), (rr, cc)))

    rng.shuffle(pairs)
    if symmetry == "rot180":
        return pairs

    # mix → flatten but keep pairs adjacent; mix of singles/pairs
    flat: list[PairOrCell] = []
    for item in pairs:
        flat.append(item)
    return flat


def _uniqueness(p: Grid) -> bool:
    return count_solutions(p, limit=2) == 1


def _try_remove(p: Grid, r: int, c: int) -> bool:
    """Try removing a single clue; keep removal only if uniqueness holds."""

    if p[r][c] == 0:
        return False
    keep = p[r][c]
    p[r][c] = 0
    ok = _uniqueness(p)
    if not ok:
        p[r][c] = keep
    return ok


def _make_minimal(p: Grid) -> Grid:
    """Enforce minimality: every clue is necessary for uniqueness."""

    # Strict single-clue minimality:
    # keep removing clues as long as uniqueness still holds.
    # Order clues by a light heuristic: remove from denser rows/cols first.
    def clue_list(grid: Grid) -> list[tuple[int, int]]:
        clues: list[tuple[int,int]] = []
        for r in range(9):
            for c in range(9):
                if grid[r][c] != 0:
                    clues.append((r,c))
        # heuristic: denser row/col first
        row_count = [sum(1 for x in grid[r] if x != 0) for r in range(9)]
        col_count = [sum(1 for r in range(9) if grid[r][c] != 0) for c in range(9)]
        clues.sort(key=lambda rc: -(row_count[rc[0]] + col_count[rc[1]]))
        return clues

    changed = True
    while changed:
        changed = False
        for r, c in clue_list(p):
            keep = p[r][c]
            p[r][c] = 0
            if _uniqueness(p):
                # removal kept; continue loop to see if we can remove more
                changed = True
            else:
                p[r][c] = keep
    # Verify strict minimality: removing any single clue breaks uniqueness.
    for r in range(9):
        for c in range(9):
            if p[r][c] == 0:
                continue
            keep = p[r][c]
            p[r][c] = 0
            still_unique = _uniqueness(p)
            p[r][c] = keep
            if still_unique:
                # Extremely rare due to ordering/race; harden by removing it and re-running once.
                p[r][c] = 0
                # Re-run a short pass to clean up any others unlocked by this removal.
                return _make_minimal(p)
    return p  # strict


def generate(
    seed: Optional[int] = None,
    *,
    target_givens: int = 28,
    minimal: bool = False,
    symmetry: Symmetry = "mix",
) -> Grid:
    """
    Create a Sudoku puzzle while preserving unique solvability.

    - target_givens: aim near this clue count (approximate)
    - minimal: enforce minimality at the end (slower)
    - symmetry: "none" | "rot180" | "mix"
    """

    rng = random.Random(seed)
    full = _random_full_solution(seed)
    puzzle = [row[:] for row in full]
    schedule = _removal_schedule(symmetry, rng)

    def remaining_clues() -> int:
        return sum(1 for rr in range(9) for cc in range(9) if puzzle[rr][cc] != 0)

    for item in schedule:
        if remaining_clues() <= target_givens:
            break

        # If symmetry is rot180, paired removals must succeed together.
        if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], tuple):
            # symmetric pair (rot180)
            (r1, c1), (r2, c2) = item  # type: ignore[misc]
            keep1, keep2 = puzzle[r1][c1], puzzle[r2][c2]
            if keep1 == 0 and keep2 == 0:
                continue
            puzzle[r1][c1] = 0
            puzzle[r2][c2] = 0
            if not _uniqueness(puzzle) or remaining_clues() < target_givens:
                puzzle[r1][c1] = keep1
                puzzle[r2][c2] = keep2
        else:
            r, c = item if isinstance(item, tuple) else item  # type: ignore[assignment]
            _try_remove(puzzle, r, c)

    if minimal:
        _make_minimal(puzzle)
    return puzzle


__all__ = ["generate"]
