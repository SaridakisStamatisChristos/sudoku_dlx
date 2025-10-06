from __future__ import annotations
from typing import List, Dict, Any, Optional
from .api import Grid, to_string, solve
from .strategies import step_once

def explain(grid: Grid, max_steps: int = 200) -> Dict[str, Any]:
    """
    Try to solve using human strategies (naked/hidden singles, locked candidates).
    Returns:
      {
        "version": "explain-1",
        "steps": [ {move...}, ... ],
        "progress": "<81-char after applying steps>",
        "solved": bool,
        "solution": "<81-char>" | None
      }
    Deterministic order and moves.
    """
    g = [row[:] for row in grid]
    steps: List[Dict[str, Any]] = []
    for _ in range(max_steps):
        m = step_once(g)
        if not m:
            break
        steps.append(m)
        # If we ever complete, stop early
        if all(g[r][c] != 0 for r in range(9) for c in range(9)):
            break
    progress = to_string(g)
    # For convenience include full solution if solvable
    solved_out: Optional[str] = None
    sres = solve([row[:] for row in grid])
    if sres is not None:
        solved_out = to_string(sres.grid)
    return {
        "version": "explain-1",
        "steps": steps,
        "progress": progress,
        "solved": progress.find(".") == -1,
        "solution": solved_out,
    }

__all__ = ["explain"]
