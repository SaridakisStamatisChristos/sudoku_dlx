# MIT License
from __future__ import annotations

import random
from copy import deepcopy
from dataclasses import dataclass
from typing import List, Tuple, Iterable, Optional

# ----------------------- Exact-cover mapping -----------------------
def col_cell(r: int, c: int) -> int: return r * 9 + c                 # 0..80
def col_row(r: int, v: int) -> int:  return 81 + r * 9 + (v - 1)      # 81..161
def col_col(c: int, v: int) -> int:  return 162 + c * 9 + (v - 1)     # 162..242
def col_box(b: int, v: int) -> int:  return 243 + b * 9 + (v - 1)     # 243..323
def box_of(r: int, c: int) -> int:   return (r // 3) * 3 + (c // 3)

ROW_COLS: List[List[int]] = []
ROW_PAYLOAD: List[Tuple[int, int, int]] = []
COL_ROWS_BITS: List[int] = [0] * 324
RCV_TO_ROWIDX: dict[Tuple[int, int, int], int] = {}

def _precompute_matrix() -> None:
    idx = 0
    for r in range(9):
        for c in range(9):
            b = box_of(r, c)
            for v in range(1, 10):
                cols = [col_cell(r, c), col_row(r, v), col_col(c, v), col_box(b, v)]
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
def iter_set_bits(x: int):
    while x:
        lsb = x & -x
        i = (lsb.bit_length() - 1)
        yield i
        x ^= lsb

def is_bit_set(x: int, i: int) -> bool:
    return (x >> i) & 1 == 1

def clear_bit(x: int, i: int) -> int:
    return x & ~(1 << i)

# --------------------------- Stats ---------------------------
@dataclass
class Stats:
    nodes: int = 0        # recursion frames visited
    branches: int = 0     # choices made
    max_depth: int = 0
    solutions: int = 0

# --------------------------- Bit-DLX core --------------------------
class BitDLX:
    def __init__(self) -> None:
        self.stats: Stats = Stats()

    def _choose_col(self, rows_mask: int, cols_mask: int) -> int | None:
        best_col = None
        best_sz = 10**9
        for c in range(324):
            if not is_bit_set(cols_mask, c):
                continue
            cand_rows = COL_ROWS_BITS[c] & rows_mask
            sz = cand_rows.bit_count()
            if sz == 0:
                return c
            if sz < best_sz:
                best_sz = sz
                best_col = c
                if sz <= 1:
                    break
        return best_col

    def _cover_row(self, rows_mask: int, cols_mask: int, row_idx: int) -> tuple[int, int]:
        cols = ROW_COLS[row_idx]
        union_rows = 0
        for c in cols:
            union_rows |= (COL_ROWS_BITS[c] & rows_mask)
        rows_mask2 = rows_mask & ~union_rows
        for c in cols:
            cols_mask = clear_bit(cols_mask, c)
        return rows_mask2, cols_mask

    def _search(
        self,
        rows_mask: int,
        cols_mask: int,
        limit: int,
        keep_one: bool,
        collect_sol: list[int],
        found: list[int],
        depth: int = 0,
    ) -> bool:
        self.stats.nodes += 1
        if depth > self.stats.max_depth:
            self.stats.max_depth = depth

        if cols_mask == 0:
            found[0] += 1
            self.stats.solutions = found[0]
            return found[0] >= limit

        c = self._choose_col(rows_mask, cols_mask)
        if c is None:
            return False
        cand = COL_ROWS_BITS[c] & rows_mask
        if cand == 0:
            return False
        for r in iter_set_bits(cand):
            self.stats.branches += 1
            rows2, cols2 = self._cover_row(rows_mask, cols_mask, r)
            if keep_one:
                collect_sol.append(r)
            if self._search(rows2, cols2, limit, keep_one, collect_sol, found, depth + 1):
                return True
            if keep_one:
                collect_sol.pop()
        return False

    def count_solutions(
        self,
        clues: list[tuple[int, int, int]],
        limit: int = 2,
        *,
        prepass: bool = True,
    ):
        """Return (count, solution_or_None). prepass=True adds naked-singles propagation."""
        self.stats = Stats()
        base_clues = clues

        if prepass:
            ok, extra = deduce_singles_from_clues(clues)
            if not ok:
                return 0, None
            if extra:
                base_clues = clues + extra

        rows_mask = ALL_ROWS_MASK
        cols_mask = ALL_COLS_MASK
        for (r, c, v) in base_clues:
            row_idx = RCV_TO_ROWIDX.get((r, c, v))
            if row_idx is None or not is_bit_set(rows_mask, row_idx):
                return 0, None
            rows_mask, cols_mask = self._cover_row(rows_mask, cols_mask, row_idx)

        found = [0]
        collect: list[int] = []
        self._search(rows_mask, cols_mask, limit, keep_one=True, collect_sol=collect, found=found)

        if found[0] == 0:
            return 0, None

        grid = [[0] * 9 for _ in range(9)]
        for (rr, cc, vv) in base_clues:
            grid[rr][cc] = vv
        for row_idx in collect:
            rr, cc, vv = ROW_PAYLOAD[row_idx]
            grid[rr][cc] = vv
        return found[0], grid

    def iter_solutions(self, clues: list[tuple[int,int,int]], limit: int | None = None, *, prepass: bool = True):
        """Yield solved grids up to 'limit' (None = unlimited)."""
        self.stats = Stats()
        base_clues = clues
        if prepass:
            ok, extra = deduce_singles_from_clues(clues)
            if not ok:
                return
            if extra:
                base_clues = clues + extra

        rows_mask = ALL_ROWS_MASK
        cols_mask = ALL_COLS_MASK
        for (r, c, v) in base_clues:
            row_idx = RCV_TO_ROWIDX.get((r, c, v))
            if row_idx is None or not is_bit_set(rows_mask, row_idx):
                return
            rows_mask, cols_mask = self._cover_row(rows_mask, cols_mask, row_idx)

        collect: list[int] = []

        def dfs(rm: int, cm: int, depth: int = 0):
            self.stats.nodes += 1
            self.stats.max_depth = max(self.stats.max_depth, depth)
            if cm == 0:
                self.stats.solutions += 1
                grid = [[0]*9 for _ in range(9)]
                for (rr,cc,vv) in base_clues: grid[rr][cc] = vv
                for rid in collect:
                    rr,cc,vv = ROW_PAYLOAD[rid]
                    grid[rr][cc] = vv
                yield grid
                return
            c = self._choose_col(rm, cm)
            if c is None:
                return
            cand = COL_ROWS_BITS[c] & rm
            if cand == 0:
                return
            for r in iter_set_bits(cand):
                self.stats.branches += 1
                rm2, cm2 = self._cover_row(rm, cm, r)
                collect.append(r)
                yield from dfs(rm2, cm2, depth + 1)
                collect.pop()
                if limit is not None and self.stats.solutions >= limit:
                    return

        yield from dfs(rows_mask, cols_mask)

SOLVER = BitDLX()

# ----------------------------- Utilities -----------------------------
def set_seed(seed: int | None):
    random.seed(seed)

def latin_base() -> list[list[int]]:
    return [[((i * 3 + i // 3 + j) % 9) + 1 for j in range(9)] for i in range(9)]

def permute_complete(grid: list[list[int]], *, rng: Optional[random.Random] = None) -> list[list[int]]:
    rng = rng or random
    g = deepcopy(grid)

    bands = [0, 1, 2]; rng.shuffle(bands)
    g = [*g[bands[0]*3:bands[0]*3+3], *g[bands[1]*3:bands[1]*3+3], *g[bands[2]*3:bands[2]*3+3]]

    for b in range(3):
        rows = [b*3 + i for i in range(3)]
        order = rows[:]; rng.shuffle(order)
        g[rows[0]], g[rows[1]], g[rows[2]] = g[order[0]], g[order[1]], g[order[2]]

    stacks = [0, 1, 2]; rng.shuffle(stacks)
    g = [[*row[stacks[0]*3:stacks[0]*3+3],
          *row[stacks[1]*3:stacks[1]*3+3],
          *row[stacks[2]*3:stacks[2]*3+3]] for row in g]

    for s in range(3):
        cols = [s*3 + i for i in range(3)]
        order = cols[:]; rng.shuffle(order)
        for r in range(9):
            row = g[r]
            row[cols[0]], row[cols[1]], row[cols[2]] = row[order[0]], row[order[1]], row[order[2]]
    return g

def random_complete(*, rng: Optional[random.Random] = None) -> list[list[int]]:
    return permute_complete(latin_base(), rng=rng)

def grid_clues(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [(r, c, grid[r][c]) for r in range(9) for c in range(9) if grid[r][c] != 0]

def print_grid(g: list[list[int]]):
    print("+-------+-------+-------+")
    for i in range(9):
        row = [str(g[i][j]) if g[i][j] else "." for j in range(9)]
        print("| " + " ".join(row[0:3]) + " | " + " ".join(row[3:6]) + " | " + " ".join(row[6:9]) + " |")
        if i % 3 == 2:
            print("+-------+-------+-------+")

def from_string(s: str) -> list[list[int]]:
    s = "".join(ch for ch in s if not ch.isspace())
    if len(s) != 81:
        raise ValueError("Grid must be 81 characters (digits 1-9 or . for empty)")
    g = [[0]*9 for _ in range(9)]
    for i, ch in enumerate(s):
        r, c = divmod(i, 9)
        g[r][c] = 0 if ch == "." else int(ch)
    return g

def to_string(g: list[list[int]]) -> str:
    return "".join("." if g[r][c] == 0 else str(g[r][c]) for r in range(9) for c in range(9))

def validate_grid(g: list[list[int]]) -> bool:
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = g[r][c]
            if not (0 <= v <= 9):
                return False
            if v == 0:
                continue
            b = box_of(r, c)
            if v in rows[r] or v in cols[c] or v in boxes[b]:
                return False
            rows[r].add(v); cols[c].add(v); boxes[b].add(v)
    return True

# ----------------------------- Symmetry ------------------------------
def rot180_pairs() -> list[tuple[tuple[int, int], tuple[int, int]]]:
    seen = set()
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(9):
        for c in range(9):
            a = (r, c); b = (8 - r, 8 - c)
            key = tuple(sorted([a, b]))
            if key not in seen:
                seen.add(key); pairs.append((a, b))
    return pairs

# ----------------------------- Prepass (naked singles) ----------------
def deduce_singles_from_clues(clues: Iterable[tuple[int, int, int]]):
    """Fill forced singles; return (ok, extra_clues)."""
    g = [[0]*9 for _ in range(9)]
    row_used = [set() for _ in range(9)]
    col_used = [set() for _ in range(9)]
    box_used = [set() for _ in range(9)]

    def place(r: int, c: int, v: int) -> bool:
        b = box_of(r, c)
        if v in row_used[r] or v in col_used[c] or v in box_used[b] or g[r][c] not in (0, v):
            return False
        g[r][c] = v
        row_used[r].add(v); col_used[c].add(v); box_used[b].add(v)
        return True

    for (r, c, v) in clues:
        if not place(r, c, v):
            return False, []

    extra: list[tuple[int, int, int]] = []
    changed = True
    while changed:
        changed = False
        for r in range(9):
            for c in range(9):
                if g[r][c] != 0:
                    continue
                b = box_of(r, c)
                cand = {v for v in range(1, 10)} - row_used[r] - col_used[c] - box_used[b]
                if len(cand) == 0:
                    return False, []
                if len(cand) == 1:
                    v = next(iter(cand))
                    place(r, c, v)
                    extra.append((r, c, v))
                    changed = True
    originals = {(r, c) for (r, c, _v) in clues}
    extra = [(r, c, g[r][c]) for r in range(9) for c in range(9)
             if g[r][c] != 0 and (r, c) not in originals]
    return True, extra

# ----------------------------- Generator -----------------------------
def generate_minimal(target_clues: int = 17, max_rounds: int = 8000,
                     symmetry: str = "mix", early_asymmetric: bool = True,
                     *, seed: Optional[int] = None, rng: Optional[random.Random] = None):
    rng = rng or (random.Random(seed) if seed is not None else random)
    full = random_complete(rng=rng)
    puzzle = deepcopy(full)

    def count_clues(p): return sum(1 for r in range(9) for c in range(9) if p[r][c] != 0)
    def unique(p):      return SOLVER.count_solutions(grid_clues(p), limit=2)[0] == 1

    if early_asymmetric:
        cells = [(r, c) for r in range(9) for c in range(9)]
        rng.shuffle(cells)
        for r, c in cells:
            if puzzle[r][c] == 0:
                continue
            backup = puzzle[r][c]; puzzle[r][c] = 0
            if not unique(puzzle):
                puzzle[r][c] = backup
            if count_clues(puzzle) <= target_clues:
                break

    if symmetry in ("rot180", "mix"):
        pairs = rot180_pairs(); rng.shuffle(pairs)
        for (a, b) in pairs:
            (r1, c1), (r2, c2) = a, b
            if puzzle[r1][c1] == 0 and puzzle[r2][c2] == 0:
                continue
            b1, b2 = puzzle[r1][c1], puzzle[r2][c2]
            puzzle[r1][c1] = 0; puzzle[r2][c2] = 0
            if not unique(puzzle):
                puzzle[r1][c1], puzzle[r2][c2] = b1, b2
            if count_clues(puzzle) <= target_clues:
                break

    if symmetry in ("none", "mix"):
        for _ in range(max_rounds):
            if count_clues(puzzle) <= target_clues:
                break
            filled = [(r, c) for r in range(9) for c in range(9) if puzzle[r][c] != 0]
            if not filled:
                break
            r, c = rng.choice(filled)
            backup = puzzle[r][c]; puzzle[r][c] = 0
            if not unique(puzzle):
                puzzle[r][c] = backup

    changed = True
    while changed:
        changed = False
        filled = [(r, c) for r in range(9) for c in range(9) if puzzle[r][c] != 0]
        rng.shuffle(filled)
        for r, c in filled:
            b = puzzle[r][c]; puzzle[r][c] = 0
            if unique(puzzle):
                changed = True
                if count_clues(puzzle) <= target_clues:
                    break
            else:
                puzzle[r][c] = b

    return puzzle, full

def is_minimal(puz: list[list[int]]) -> bool:
    for r in range(9):
        for c in range(9):
            if puz[r][c] == 0:
                continue
            b = puz[r][c]; puz[r][c] = 0
            u = SOLVER.count_solutions(grid_clues(puz), limit=2)[0] == 1
            puz[r][c] = b
            if u:
                return False
    return True

def hardness_estimate(grid: list[list[int]]) -> float:
    """Heuristic difficulty score based on clue count, prepass gain, and node count."""
    initial_clues = sum(1 for r in range(9) for c in range(9) if grid[r][c] != 0)
    ok, extra = deduce_singles_from_clues(grid_clues(grid))
    if not ok:
        return float("inf")
    prepass_gain = len(extra)
    _ = SOLVER.count_solutions(grid_clues(grid), limit=1)
    nodes = max(1, SOLVER.stats.nodes)
    score = (50 - initial_clues) * 0.5 + (max(0, 10 - prepass_gain)) * 0.7 + (nodes ** 0.25)
    return round(score, 2)
