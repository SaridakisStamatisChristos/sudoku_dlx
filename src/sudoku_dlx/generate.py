from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Literal, Optional

from .api import Grid, count_solutions, solve
from .logic import HumanDifficulty, HumanRating, human_rate
from .rating import rate
from .solver import random_complete

Symmetry = Literal["none", "rot180", "mix"]
Cell = tuple[int, int]
RemovalGroup = tuple[Cell, ...]

_VALID_SYMMETRIES = {"none", "rot180", "mix"}
_DEFAULT_GIVENS_BY_DIFFICULTY: dict[HumanDifficulty, int] = {
    "easy": 40,
    "medium": 34,
    "hard": 30,
    "expert": 26,
}


@dataclass(frozen=True)
class GenerationResult:
    grid: Grid
    solution: Grid
    seed: Optional[int]
    attempts: int
    givens: int
    symmetry: Symmetry
    minimality: str
    machine_difficulty: float
    human_difficulty: HumanRating


def _random_full_solution(seed: Optional[int]) -> Grid:
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
    changed = True
    while changed:
        changed = False
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
    changed = True
    while changed:
        changed = False
        for group in _rot180_orbits():
            if _try_remove_group(grid, group):
                changed = True

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


def _minimality_name(minimal: bool, symmetry: Symmetry) -> str:
    if not minimal:
        return "none"
    return "orbit" if symmetry == "rot180" else "strict"


def generate(
    seed: Optional[int] = None,
    *,
    target_givens: int = 28,
    minimal: bool = False,
    symmetry: Symmetry = "mix",
) -> Grid:
    """Create a uniquely solvable Sudoku puzzle."""

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


def generate_result(
    seed: Optional[int] = None,
    *,
    target_givens: int = 28,
    minimal: bool = False,
    symmetry: Symmetry = "mix",
) -> GenerationResult:
    """Generate one puzzle and return reproducible solver/rating metadata."""

    grid = generate(
        seed=seed,
        target_givens=target_givens,
        minimal=minimal,
        symmetry=symmetry,
    )
    solved = solve(grid, collect_stats=False)
    if solved is None:
        raise AssertionError("generator produced an unsatisfiable puzzle")
    return GenerationResult(
        grid=[row[:] for row in grid],
        solution=[row[:] for row in solved.grid],
        seed=seed,
        attempts=1,
        givens=_remaining_clues(grid),
        symmetry=symmetry,
        minimality=_minimality_name(minimal, symmetry),
        machine_difficulty=rate(grid),
        human_difficulty=human_rate(grid),
    )


def generate_rated(
    human_difficulty: HumanDifficulty,
    seed: Optional[int] = None,
    *,
    target_givens: Optional[int] = None,
    minimal: bool = False,
    symmetry: Symmetry = "mix",
    max_attempts: int = 64,
) -> GenerationResult:
    """Generate a puzzle whose deterministic human difficulty label matches the target."""

    if human_difficulty not in _DEFAULT_GIVENS_BY_DIFFICULTY:
        raise ValueError("human_difficulty must be one of: easy, medium, hard, expert")
    if type(max_attempts) is not int or max_attempts < 1:
        raise ValueError("max_attempts must be an integer >= 1")

    givens = (
        _DEFAULT_GIVENS_BY_DIFFICULTY[human_difficulty]
        if target_givens is None
        else target_givens
    )
    if type(givens) is not int or not 17 <= givens <= 81:
        raise ValueError("target_givens must be an integer in 17..81")

    rng = random.Random(seed)
    for attempt in range(1, max_attempts + 1):
        candidate_seed = rng.randrange(2**31 - 1)
        result = generate_result(
            seed=candidate_seed,
            target_givens=givens,
            minimal=minimal,
            symmetry=symmetry,
        )
        if result.human_difficulty.label == human_difficulty:
            return GenerationResult(
                grid=result.grid,
                solution=result.solution,
                seed=candidate_seed,
                attempts=attempt,
                givens=result.givens,
                symmetry=result.symmetry,
                minimality=result.minimality,
                machine_difficulty=result.machine_difficulty,
                human_difficulty=result.human_difficulty,
            )

    raise RuntimeError(
        f"could not generate a {human_difficulty!r} puzzle in {max_attempts} attempts"
    )


__all__ = [
    "GenerationResult",
    "Symmetry",
    "generate",
    "generate_rated",
    "generate_result",
]
