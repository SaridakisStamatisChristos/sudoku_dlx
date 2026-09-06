from __future__ import annotations

from typing import Any, Dict, Optional

from .api import Grid, is_valid, solve, to_string
from .logic import logical_solve


def explain(grid: Grid, max_steps: int = 200) -> Dict[str, Any]:
    """
    Try to solve using the deterministic human-strategy stack.

    Candidate eliminations persist across steps through ``LogicalState``.
    The public dictionary shape remains compatible with explain-1.
    """

    if type(max_steps) is not int or max_steps < 0:
        raise ValueError("max_steps must be an integer >= 0")

    steps: list[dict[str, Any]] = []
    progress_grid = [row[:] for row in grid]
    solved_logically = False

    if is_valid(grid):
        logical = logical_solve(grid, max_steps=max_steps)
        progress_grid = logical.grid
        steps = logical.steps
        solved_logically = logical.solved

    progress = to_string(progress_grid)

    solved_out: Optional[str] = None
    if solved_logically:
        solved_out = progress
    else:
        sres = solve([row[:] for row in grid])
        if sres is not None:
            solved_out = to_string(sres.grid)

    return {
        "version": "explain-1",
        "steps": steps,
        "progress": progress,
        "solved": solved_logically,
        "solution": solved_out,
    }


__all__ = ["explain"]
