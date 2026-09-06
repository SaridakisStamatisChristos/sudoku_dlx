from __future__ import annotations

from typing import Any, Dict, List, Optional

from .api import Grid, solve, to_string
from .strategies import (
    apply_box_line_claiming,
    apply_hidden_pair,
    apply_hidden_single,
    apply_hidden_triple,
    apply_locked_candidates_pointing,
    apply_naked_pair,
    apply_naked_single,
    apply_naked_triple,
    apply_simple_coloring,
    apply_swordfish,
    apply_x_wing,
    candidates,
)

Cand = List[List[set[int]]]

_PLACEMENT_STRATEGIES = (apply_naked_single, apply_hidden_single)
_ELIMINATION_STRATEGIES = (
    apply_locked_candidates_pointing,
    apply_box_line_claiming,
    apply_naked_pair,
    apply_hidden_pair,
    apply_x_wing,
    apply_naked_triple,
    apply_hidden_triple,
    apply_swordfish,
    apply_simple_coloring,
)


def _candidate_state_has_contradiction(grid: Grid, cand: Cand) -> bool:
    return any(grid[r][c] == 0 and not cand[r][c] for r in range(9) for c in range(9))


def _refresh_after_placement(grid: Grid, cand: Cand) -> None:
    """Apply new grid constraints without resurrecting prior logical eliminations."""

    legal = candidates(grid)
    for r in range(9):
        for c in range(9):
            if grid[r][c] != 0:
                cand[r][c].clear()
            else:
                cand[r][c].intersection_update(legal[r][c])
    if _candidate_state_has_contradiction(grid, cand):
        raise RuntimeError("logical solver reached a contradictory candidate state")


def _step_once_stateful(grid: Grid, cand: Cand) -> Optional[Dict[str, Any]]:
    """Apply one logical move while preserving candidate eliminations across calls."""

    for strategy in _PLACEMENT_STRATEGIES:
        move = strategy(grid, cand)
        if move:
            _refresh_after_placement(grid, cand)
            return move

    for strategy in _ELIMINATION_STRATEGIES:
        move = strategy(grid, cand)
        if move:
            if _candidate_state_has_contradiction(grid, cand):
                raise RuntimeError(
                    f"logical strategy {move.get('strategy', '<unknown>')} produced a contradiction"
                )
            return move
    return None


def explain(grid: Grid, max_steps: int = 200) -> Dict[str, Any]:
    """
    Try to solve using the deterministic human-strategy stack.

    Candidate eliminations are persistent for the lifetime of this explanation
    run. Placements refresh only the newly illegal candidates, so prior logical
    eliminations are never silently resurrected.

    Returns::

      {
        "version": "explain-1",
        "steps": [ {move...}, ... ],
        "progress": "<81-char after applying steps>",
        "solved": bool,
        "solution": "<81-char>" | None
      }
    """

    g = [row[:] for row in grid]
    cand = candidates(g)
    steps: List[Dict[str, Any]] = []

    if not _candidate_state_has_contradiction(g, cand):
        for _ in range(max_steps):
            move = _step_once_stateful(g, cand)
            if not move:
                break
            steps.append(move)
            if all(g[r][c] != 0 for r in range(9) for c in range(9)):
                break

    progress = to_string(g)

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
