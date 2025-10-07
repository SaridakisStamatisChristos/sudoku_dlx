from __future__ import annotations

"""SAT cross-check utilities using python-sat (optional extra)."""

from typing import Iterable, List, Optional

Grid = List[List[int]]


def _var(r: int, c: int, d: int) -> int:
    """Map (row, col, digit) triples to CNF variables in [1, 729]."""

    return r * 81 + c * 9 + d + 1


def _encode_cnf(grid: Grid) -> list[list[int]]:
    cnf: list[list[int]] = []
    # 1) Each cell has at least one digit
    for r in range(9):
        for c in range(9):
            cnf.append([_var(r, c, d) for d in range(9)])
    # 2) Each cell has at most one digit
    for r in range(9):
        for c in range(9):
            for d1 in range(9):
                for d2 in range(d1 + 1, 9):
                    cnf.append([-_var(r, c, d1), -_var(r, c, d2)])
    # 3) Rows: each digit appears exactly once
    for r in range(9):
        for d in range(9):
            cnf.append([_var(r, c, d) for c in range(9)])
            for c1 in range(9):
                for c2 in range(c1 + 1, 9):
                    cnf.append([-_var(r, c1, d), -_var(r, c2, d)])
    # 4) Columns: each digit appears exactly once
    for c in range(9):
        for d in range(9):
            cnf.append([_var(r, c, d) for r in range(9)])
            for r1 in range(9):
                for r2 in range(r1 + 1, 9):
                    cnf.append([-_var(r1, c, d), -_var(r2, c, d)])
    # 5) Boxes: each digit appears exactly once
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            cells = [(r, c) for r in range(br, br + 3) for c in range(bc, bc + 3)]
            for d in range(9):
                cnf.append([_var(r, c, d) for (r, c) in cells])
                for i in range(9):
                    for j in range(i + 1, 9):
                        r1, c1 = cells[i]
                        r2, c2 = cells[j]
                        cnf.append([-_var(r1, c1, d), -_var(r2, c2, d)])
    # 6) Givens
    for r in range(9):
        for c in range(9):
            v = grid[r][c]
            if v:
                cnf.append([_var(r, c, v - 1)])
    return cnf


def cnf_dimacs_lines(grid: Grid) -> Iterable[str]:
    """Yield DIMACS CNF lines for ``grid`` using variables in ``[1, 729]``."""

    cnf = _encode_cnf(grid)
    num_vars = 9 * 9 * 9
    num_clauses = len(cnf)
    yield f"p cnf {num_vars} {num_clauses}"
    for clause in cnf:
        literals = " ".join(str(int(lit)) for lit in clause)
        yield f"{literals} 0"


def sat_solve(grid: Grid) -> Optional[Grid]:
    """Solve a Sudoku grid via SAT; returns the solved grid or ``None`` if unavailable."""

    try:
        from pysat.solvers import Minisat22  # type: ignore import-not-found
    except Exception:
        return None

    cnf = _encode_cnf(grid)
    with Minisat22(bootstrap_with=cnf) as solver:
        if not solver.solve():
            return None
        model = solver.get_model()

    solved: Grid = [[0] * 9 for _ in range(9)]
    for r in range(9):
        for c in range(9):
            for d in range(9):
                if _var(r, c, d) in model:
                    solved[r][c] = d + 1
                    break
    return solved


__all__ = ["sat_solve", "cnf_dimacs_lines"]
