# MIT License
from __future__ import annotations

import random
from copy import deepcopy
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional, Tuple

Clue = tuple[int, int, int]
Grid = list[list[int]]

# ----------------------- Exact-cover mapping -----------------------
def col_cell(r: int, c: int) -> int:
    return r * 9 + c  # 0..80


def col_row(r: int, v: int) -> int:
    return 81 + r * 9 + (v - 1)  # 81..161


def col_col(c: int, v: int) -> int:
    return 162 + c * 9 + (v - 1)  # 162..242


def col_box(b: int, v: int) -> int:
    return 243 + b * 9 + (v - 1)  # 243..323


def box_of(r: int, c: int) -> int:
    return (r // 3) * 3 + (c // 3)


ROW_COLS: List[Tuple[int, int, int, int]] = []
ROW_PAYLOAD: List[Tuple[int, int, int]] = []
COL_ROWS_BITS: List[int] = [0] * 324
RCV_TO_ROWIDX: dict[Tuple[int, int, int], int] = {}


def _precompute_matrix() -> None:
    idx = 0
    for r in range(9):
        for c in range(9):
            b = box_of(r, c)
            for v in range(1, 10):
                cols = (
                    col_cell(r, c),
                    col_row(r, v),
                    col_col(c, v),
                    col_box(b, v),
                )
                ROW_COLS.append(cols)
                ROW_PAYLOAD.append((r, c, v))
                RCV_TO_ROWIDX[(r, c, v)] = idx
                mask = 1 << idx
                for col in cols:
                    COL_ROWS_BITS[col] |= mask
                idx += 1


_precompute_matrix()

ALL_ROWS_MASK = (1 << 729) - 1
ALL_COLS_MASK = (1 << 324) - 1


# --------------------------- Bit helpers ---------------------------
def iter_set_bits(x: int) -> Iterator[int]:
    while x:
        lsb = x & -x
        yield lsb.bit_length() - 1
        x ^= lsb


def is_bit_set(x: int, i: int) -> bool:
    return (x >> i) & 1 == 1


def clear_bit(x: int, i: int) -> int:
    return x & ~(1 << i)


# --------------------------- Stats ---------------------------
@dataclass
class Stats:
    """Deterministic search-work counters for one BitDLX invocation."""

    nodes: int = 0
    branches: int = 0
    backtracks: int = 0
    max_depth: int = 0
    solutions: int = 0


def _normalize_clues(clues: Iterable[Clue]) -> list[Clue] | None:
    """Validate and de-duplicate clues while preserving the first-seen order."""

    out: list[Clue] = []
    seen: dict[tuple[int, int], int] = {}
    try:
        iterator = iter(clues)
    except TypeError:
        return None

    for clue in iterator:
        if not isinstance(clue, tuple) or len(clue) != 3:
            return None
        r, c, v = clue
        if not all(type(x) is int for x in (r, c, v)):
            return None
        if not (0 <= r < 9 and 0 <= c < 9 and 1 <= v <= 9):
            return None
        previous = seen.get((r, c))
        if previous is not None:
            if previous != v:
                return None
            continue
        seen[(r, c)] = v
        out.append((r, c, v))
    return out


# --------------------------- Bit-DLX core --------------------------
class BitDLX:
    """
    Exact-cover Sudoku engine backed by Python integer bitsets.

    A BitDLX instance exposes mutable ``stats`` for compatibility. Public package
    APIs create an engine per invocation, so ordinary ``sudoku_dlx.solve`` and
    ``count_solutions`` calls do not share mutable search state.
    """

    def __init__(self) -> None:
        self.stats = Stats()

    @staticmethod
    def _choose_col(rows_mask: int, cols_mask: int) -> int | None:
        best_col: int | None = None
        best_size = 10**9
        active = cols_mask
        while active:
            lsb = active & -active
            c = lsb.bit_length() - 1
            active ^= lsb
            size = (COL_ROWS_BITS[c] & rows_mask).bit_count()
            if size == 0:
                return c
            if size < best_size:
                best_size = size
                best_col = c
                if size == 1:
                    break
        return best_col

    @staticmethod
    def _cover_row(rows_mask: int, cols_mask: int, row_idx: int) -> tuple[int, int]:
        union_rows = 0
        for c in ROW_COLS[row_idx]:
            union_rows |= COL_ROWS_BITS[c] & rows_mask
            cols_mask = clear_bit(cols_mask, c)
        return rows_mask & ~union_rows, cols_mask

    def _prepare_state(
        self,
        clues: Iterable[Clue],
        *,
        prepass: bool,
    ) -> tuple[int, int, list[Clue]] | None:
        normalized = _normalize_clues(clues)
        if normalized is None:
            return None

        base_clues = normalized
        if prepass:
            ok, extra = deduce_singles_from_clues(normalized)
            if not ok:
                return None
            if extra:
                base_clues = normalized + extra

        rows_mask = ALL_ROWS_MASK
        cols_mask = ALL_COLS_MASK
        for r, c, v in base_clues:
            row_idx = RCV_TO_ROWIDX[(r, c, v)]
            if not is_bit_set(rows_mask, row_idx):
                return None
            rows_mask, cols_mask = self._cover_row(rows_mask, cols_mask, row_idx)
        return rows_mask, cols_mask, base_clues

    def count_solutions(
        self,
        clues: Iterable[Clue],
        limit: int = 2,
        *,
        prepass: bool = True,
    ) -> tuple[int, Grid | None]:
        """
        Count solutions up to ``limit`` and return the first complete solution.

        ``limit`` must be >= 1. The returned solution is retained independently
        from the DFS path, so it remains complete even when the search continues
        after the first solution to establish uniqueness.
        """

        if type(limit) is not int or limit < 1:
            raise ValueError("limit must be an integer >= 1")

        self.stats = Stats()
        prepared = self._prepare_state(clues, prepass=prepass)
        if prepared is None:
            return 0, None

        rows_mask, cols_mask, base_clues = prepared
        found = 0
        path: list[int] = []
        first_solution: list[int] | None = None
        stats = self.stats

        def search(rm: int, cm: int, depth: int = 0) -> bool:
            nonlocal found, first_solution
            stats.nodes += 1
            stats.max_depth = max(stats.max_depth, depth)

            if cm == 0:
                found += 1
                stats.solutions = found
                if first_solution is None:
                    first_solution = path.copy()
                return found >= limit

            c = self._choose_col(rm, cm)
            if c is None:
                return False

            candidates = COL_ROWS_BITS[c] & rm
            if candidates == 0:
                return False

            for row_idx in iter_set_bits(candidates):
                stats.branches += 1
                before = found
                rm2, cm2 = self._cover_row(rm, cm, row_idx)
                path.append(row_idx)
                stop = search(rm2, cm2, depth + 1)
                path.pop()
                if stop:
                    return True
                if found == before:
                    stats.backtracks += 1
            return False

        search(rows_mask, cols_mask)
        if found == 0 or first_solution is None:
            return 0, None

        grid: Grid = [[0] * 9 for _ in range(9)]
        for r, c, v in base_clues:
            grid[r][c] = v
        for row_idx in first_solution:
            r, c, v = ROW_PAYLOAD[row_idx]
            grid[r][c] = v
        return found, grid

    def iter_solutions(
        self,
        clues: Iterable[Clue],
        limit: int | None = None,
        *,
        prepass: bool = True,
    ) -> Iterator[Grid]:
        """Yield complete solutions, optionally stopping after ``limit`` results."""

        if limit is not None and (type(limit) is not int or limit < 1):
            raise ValueError("limit must be None or an integer >= 1")

        self.stats = Stats()
        prepared = self._prepare_state(clues, prepass=prepass)
        if prepared is None:
            return

        rows_mask, cols_mask, base_clues = prepared
        path: list[int] = []
        stats = self.stats

        def dfs(rm: int, cm: int, depth: int = 0) -> Iterator[Grid]:
            stats.nodes += 1
            stats.max_depth = max(stats.max_depth, depth)

            if cm == 0:
                stats.solutions += 1
                grid: Grid = [[0] * 9 for _ in range(9)]
                for r, c, v in base_clues:
                    grid[r][c] = v
                for row_idx in path:
                    r, c, v = ROW_PAYLOAD[row_idx]
                    grid[r][c] = v
                yield grid
                return

            c = self._choose_col(rm, cm)
            if c is None:
                return
            candidates = COL_ROWS_BITS[c] & rm
            if candidates == 0:
                return

            for row_idx in iter_set_bits(candidates):
                if limit is not None and stats.solutions >= limit:
                    return
                stats.branches += 1
                before = stats.solutions
                rm2, cm2 = self._cover_row(rm, cm, row_idx)
                path.append(row_idx)
                yield from dfs(rm2, cm2, depth + 1)
                path.pop()
                if stats.solutions == before:
                    stats.backtracks += 1

        yield from dfs(rows_mask, cols_mask)


# Compatibility singleton. Prefer the public API or a dedicated BitDLX instance.
SOLVER = BitDLX()


# ----------------------------- Utilities -----------------------------
def set_seed(seed: int | None) -> None:
    random.seed(seed)


def latin_base() -> Grid:
    return [[((i * 3 + i // 3 + j) % 9) + 1 for j in range(9)] for i in range(9)]


def permute_complete(grid: Grid, *, rng: Optional[random.Random] = None) -> Grid:
    rng = rng or random
    g = deepcopy(grid)

    bands = [0, 1, 2]
    rng.shuffle(bands)
    g = [
        *g[bands[0] * 3 : bands[0] * 3 + 3],
        *g[bands[1] * 3 : bands[1] * 3 + 3],
        *g[bands[2] * 3 : bands[2] * 3 + 3],
    ]

    for b in range(3):
        rows = [b * 3 + i for i in range(3)]
        order = rows[:]
        rng.shuffle(order)
        g[rows[0]], g[rows[1]], g[rows[2]] = g[order[0]], g[order[1]], g[order[2]]

    stacks = [0, 1, 2]
    rng.shuffle(stacks)
    g = [
        [
            *row[stacks[0] * 3 : stacks[0] * 3 + 3],
            *row[stacks[1] * 3 : stacks[1] * 3 + 3],
            *row[stacks[2] * 3 : stacks[2] * 3 + 3],
        ]
        for row in g
    ]

    for s in range(3):
        cols = [s * 3 + i for i in range(3)]
        order = cols[:]
        rng.shuffle(order)
        for row in g:
            row[cols[0]], row[cols[1]], row[cols[2]] = (
                row[order[0]],
                row[order[1]],
                row[order[2]],
            )

    digits = list(range(1, 10))
    shuffled = digits[:]
    rng.shuffle(shuffled)
    remap = dict(zip(digits, shuffled))
    return [[remap[v] for v in row] for row in g]


def random_complete(*, rng: Optional[random.Random] = None) -> Grid:
    return permute_complete(latin_base(), rng=rng)


def _well_formed_grid(grid: object) -> bool:
    if not isinstance(grid, list) or len(grid) != 9:
        return False
    for row in grid:
        if not isinstance(row, list) or len(row) != 9:
            return False
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return False
    return True


def grid_clues(grid: Grid) -> list[Clue]:
    if not _well_formed_grid(grid):
        raise ValueError("grid must be a 9x9 list of integers in 0..9")
    return [(r, c, grid[r][c]) for r in range(9) for c in range(9) if grid[r][c] != 0]


def print_grid(grid: Grid) -> None:
    if not _well_formed_grid(grid):
        raise ValueError("grid must be a 9x9 list of integers in 0..9")
    print("+-------+-------+-------+")
    for i in range(9):
        row = [str(grid[i][j]) if grid[i][j] else "." for j in range(9)]
        print(
            "| "
            + " ".join(row[0:3])
            + " | "
            + " ".join(row[3:6])
            + " | "
            + " ".join(row[6:9])
            + " |"
        )
        if i % 3 == 2:
            print("+-------+-------+-------+")


def from_string(s: str) -> Grid:
    text = "".join(ch for ch in s if not ch.isspace())
    if len(text) != 81:
        raise ValueError("Grid must be 81 characters (digits 1-9, 0, or . for empty)")
    grid: Grid = [[0] * 9 for _ in range(9)]
    for i, ch in enumerate(text):
        r, c = divmod(i, 9)
        if ch in ".0":
            grid[r][c] = 0
        elif ch in "123456789":
            grid[r][c] = int(ch)
        else:
            raise ValueError(f"bad grid character at position {i}: {ch!r}")
    return grid


def to_string(grid: Grid) -> str:
    if not _well_formed_grid(grid):
        raise ValueError("grid must be a 9x9 list of integers in 0..9")
    return "".join(
        "." if grid[r][c] == 0 else str(grid[r][c]) for r in range(9) for c in range(9)
    )


def validate_grid(grid: Grid) -> bool:
    if not _well_formed_grid(grid):
        return False
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = grid[r][c]
            if v == 0:
                continue
            b = box_of(r, c)
            if v in rows[r] or v in cols[c] or v in boxes[b]:
                return False
            rows[r].add(v)
            cols[c].add(v)
            boxes[b].add(v)
    return True


# ----------------------------- Symmetry ------------------------------
def rot180_pairs() -> list[tuple[tuple[int, int], tuple[int, int]]]:
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(9):
        for c in range(9):
            a = (r, c)
            b = (8 - r, 8 - c)
            key = tuple(sorted((a, b)))
            if key not in seen:
                seen.add(key)
                pairs.append((a, b))
    return pairs


# ----------------------------- Prepass ------------------------------
def deduce_singles_from_clues(clues: Iterable[Clue]) -> tuple[bool, list[Clue]]:
    """Fill forced naked singles and return ``(consistent, extra_clues)``."""

    normalized = _normalize_clues(clues)
    if normalized is None:
        return False, []

    grid: Grid = [[0] * 9 for _ in range(9)]
    row_used = [set() for _ in range(9)]
    col_used = [set() for _ in range(9)]
    box_used = [set() for _ in range(9)]

    for r, c, v in normalized:
        b = box_of(r, c)
        if v in row_used[r] or v in col_used[c] or v in box_used[b]:
            return False, []
        grid[r][c] = v
        row_used[r].add(v)
        col_used[c].add(v)
        box_used[b].add(v)

    changed = True
    while changed:
        changed = False
        for r in range(9):
            for c in range(9):
                if grid[r][c] != 0:
                    continue
                b = box_of(r, c)
                candidates = set(range(1, 10)) - row_used[r] - col_used[c] - box_used[b]
                if not candidates:
                    return False, []
                if len(candidates) == 1:
                    value = next(iter(candidates))
                    grid[r][c] = value
                    row_used[r].add(value)
                    col_used[c].add(value)
                    box_used[b].add(value)
                    changed = True

    originals = {(r, c) for r, c, _ in normalized}
    extra = [
        (r, c, grid[r][c])
        for r in range(9)
        for c in range(9)
        if grid[r][c] != 0 and (r, c) not in originals
    ]
    return True, extra


# ----------------------------- Legacy generator -----------------------------
def generate_minimal(
    target_clues: int = 17,
    max_rounds: int = 8000,
    symmetry: str = "mix",
    early_asymmetric: bool = True,
    *,
    seed: Optional[int] = None,
    rng: Optional[random.Random] = None,
) -> tuple[Grid, Grid]:
    if type(target_clues) is not int or not 17 <= target_clues <= 81:
        raise ValueError("target_clues must be an integer in 17..81")
    if type(max_rounds) is not int or max_rounds < 0:
        raise ValueError("max_rounds must be a non-negative integer")
    if symmetry not in {"none", "rot180", "mix"}:
        raise ValueError("symmetry must be one of: none, rot180, mix")

    rng = rng or (random.Random(seed) if seed is not None else random)
    full = random_complete(rng=rng)
    puzzle = deepcopy(full)
    solver = BitDLX()

    def count_clues(p: Grid) -> int:
        return sum(1 for r in range(9) for c in range(9) if p[r][c] != 0)

    def unique(p: Grid) -> bool:
        return solver.count_solutions(grid_clues(p), limit=2)[0] == 1

    if early_asymmetric and symmetry != "rot180":
        cells = [(r, c) for r in range(9) for c in range(9)]
        rng.shuffle(cells)
        for r, c in cells:
            if puzzle[r][c] == 0:
                continue
            backup = puzzle[r][c]
            puzzle[r][c] = 0
            if not unique(puzzle):
                puzzle[r][c] = backup
            if count_clues(puzzle) <= target_clues:
                break

    if symmetry in {"rot180", "mix"}:
        pairs = rot180_pairs()
        rng.shuffle(pairs)
        for (r1, c1), (r2, c2) in pairs:
            if puzzle[r1][c1] == 0 and puzzle[r2][c2] == 0:
                continue
            b1, b2 = puzzle[r1][c1], puzzle[r2][c2]
            puzzle[r1][c1] = 0
            puzzle[r2][c2] = 0
            if not unique(puzzle):
                puzzle[r1][c1], puzzle[r2][c2] = b1, b2
            if count_clues(puzzle) <= target_clues:
                break

    if symmetry in {"none", "mix"}:
        for _ in range(max_rounds):
            if count_clues(puzzle) <= target_clues:
                break
            filled = [(r, c) for r in range(9) for c in range(9) if puzzle[r][c] != 0]
            if not filled:
                break
            r, c = rng.choice(filled)
            backup = puzzle[r][c]
            puzzle[r][c] = 0
            if not unique(puzzle):
                puzzle[r][c] = backup

    # Strict single-clue minimality for the legacy function. For exact
    # rotational symmetry use the modern generate(..., symmetry="rot180")
    # without the strict-minimal post-pass.
    changed = True
    while changed:
        changed = False
        filled = [(r, c) for r in range(9) for c in range(9) if puzzle[r][c] != 0]
        rng.shuffle(filled)
        for r, c in filled:
            backup = puzzle[r][c]
            puzzle[r][c] = 0
            if unique(puzzle):
                changed = True
            else:
                puzzle[r][c] = backup

    return puzzle, full


def is_minimal(puzzle: Grid) -> bool:
    if not validate_grid(puzzle):
        return False
    solver = BitDLX()
    if solver.count_solutions(grid_clues(puzzle), limit=2)[0] != 1:
        return False
    for r in range(9):
        for c in range(9):
            if puzzle[r][c] == 0:
                continue
            candidate = [row[:] for row in puzzle]
            candidate[r][c] = 0
            if solver.count_solutions(grid_clues(candidate), limit=2)[0] == 1:
                return False
    return True


def hardness_estimate(grid: Grid) -> float:
    """Legacy deterministic hardness estimate based on clues, prepass gain, and nodes."""

    if not validate_grid(grid):
        return float("inf")
    initial_clues = sum(1 for r in range(9) for c in range(9) if grid[r][c] != 0)
    ok, extra = deduce_singles_from_clues(grid_clues(grid))
    if not ok:
        return float("inf")
    solver = BitDLX()
    count, _ = solver.count_solutions(grid_clues(grid), limit=1)
    if count == 0:
        return float("inf")
    nodes = max(1, solver.stats.nodes)
    score = (50 - initial_clues) * 0.5 + max(0, 10 - len(extra)) * 0.7 + nodes**0.25
    return round(score, 2)
