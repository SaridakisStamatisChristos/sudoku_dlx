from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Dict, List, Literal, Optional

from .api import Grid, is_valid
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
Move = Dict[str, Any]
HumanDifficulty = Literal["easy", "medium", "hard", "expert"]

HUMAN_DIFFICULTY_VERSION = "1"

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

# Strategy names are the exact public move names emitted by strategies.py.
# Keep the generic aliases for compatibility with externally supplied traces.
_STRATEGY_WEIGHT = {
    "naked_single": 1.0,
    "hidden_single": 2.0,
    "locked_pointing_row": 3.0,
    "locked_pointing_col": 3.0,
    "box_line_row": 3.0,
    "box_line_col": 3.0,
    "naked_pair": 4.0,
    "hidden_pair": 4.0,
    "naked_triple": 5.0,
    "hidden_triple": 5.0,
    "x_wing": 6.0,
    "x_wing_row": 6.0,
    "x_wing_col": 6.0,
    "swordfish": 7.5,
    "swordfish_row": 7.5,
    "swordfish_col": 7.5,
    "simple_coloring": 8.5,
}


class _LogicalContradiction(RuntimeError):
    """Internal signal that the human candidate state became impossible."""


@dataclass
class LogicalResult:
    grid: Grid
    steps: List[Move]
    solved: bool
    stalled: bool
    contradiction: bool
    limit_reached: bool
    hardest_strategy: Optional[str]


@dataclass(frozen=True)
class HumanRating:
    version: str
    score: float
    label: HumanDifficulty
    solved_logically: bool
    steps: int
    placements: int
    eliminations: int
    hardest_strategy: Optional[str]
    contradiction: bool = False


class LogicalState:
    """Persistent candidate state for deterministic human-style solving."""

    def __init__(self, grid: Grid):
        if not is_valid(grid):
            raise ValueError("grid must be a valid 9x9 Sudoku state")
        self.grid: Grid = [row[:] for row in grid]
        self.candidates: Cand = candidates(self.grid)
        self.steps: List[Move] = []
        self.contradiction = self._has_contradiction()
        self.hardest_strategy: Optional[str] = None

    @staticmethod
    def _unit_cells(kind: str, idx: int) -> list[tuple[int, int]]:
        if kind == "row":
            return [(idx, c) for c in range(9)]
        if kind == "col":
            return [(r, idx) for r in range(9)]
        br, bc = (idx // 3) * 3, (idx % 3) * 3
        return [(br + dr, bc + dc) for dr in range(3) for dc in range(3)]

    def _has_contradiction(self) -> bool:
        # Cell-level contradiction: an unfilled cell has no remaining value.
        if any(
            self.grid[r][c] == 0 and not self.candidates[r][c]
            for r in range(9)
            for c in range(9)
        ):
            return True

        # Unit-level contradiction: a digit missing from a row/column/box has
        # no candidate position left. This catches unsound eliminations before
        # they necessarily collapse a particular cell to the empty set.
        for kind in ("row", "col", "box"):
            for idx in range(9):
                cells = self._unit_cells(kind, idx)
                placed = {self.grid[r][c] for r, c in cells if self.grid[r][c] != 0}
                for digit in range(1, 10):
                    if digit in placed:
                        continue
                    if not any(
                        self.grid[r][c] == 0 and digit in self.candidates[r][c]
                        for r, c in cells
                    ):
                        return True
        return False

    def _refresh_after_placement(self) -> None:
        legal = candidates(self.grid)
        for r in range(9):
            for c in range(9):
                if self.grid[r][c] != 0:
                    self.candidates[r][c].clear()
                else:
                    self.candidates[r][c].intersection_update(legal[r][c])
        self.contradiction = self._has_contradiction()
        if self.contradiction:
            raise _LogicalContradiction("logical solver reached a contradictory candidate state")

    def _record(self, move: Move) -> Move:
        self.steps.append(move)
        strategy = str(move.get("strategy", ""))
        if strategy and (
            self.hardest_strategy is None
            or _STRATEGY_WEIGHT.get(strategy, 0.0)
            > _STRATEGY_WEIGHT.get(self.hardest_strategy, 0.0)
        ):
            self.hardest_strategy = strategy
        return move

    def step(self) -> Optional[Move]:
        if self.contradiction:
            return None

        for strategy in _PLACEMENT_STRATEGIES:
            move = strategy(self.grid, self.candidates)
            if move:
                self._refresh_after_placement()
                return self._record(move)

        for strategy in _ELIMINATION_STRATEGIES:
            move = strategy(self.grid, self.candidates)
            if move:
                self.contradiction = self._has_contradiction()
                if self.contradiction:
                    raise _LogicalContradiction(
                        f"logical strategy {move.get('strategy', '<unknown>')} produced a contradiction"
                    )
                return self._record(move)
        return None

    def solved(self) -> bool:
        return all(value != 0 for row in self.grid for value in row)

    def run(self, max_steps: int = 500) -> LogicalResult:
        if type(max_steps) is not int or max_steps < 0:
            raise ValueError("max_steps must be an integer >= 0")

        limit_reached = False
        for _ in range(max_steps):
            if self.solved():
                break
            try:
                move = self.step()
            except _LogicalContradiction:
                # step() deliberately remains strict for callers debugging one
                # strategy at a time. A full logical run, however, has a public
                # contradiction result and must return it rather than crash.
                break
            if move is None:
                break
        else:
            limit_reached = not self.solved()

        solved = self.solved() and not self.contradiction
        stalled = not solved and not self.contradiction and not limit_reached
        return LogicalResult(
            grid=[row[:] for row in self.grid],
            steps=[dict(step) for step in self.steps],
            solved=solved,
            stalled=stalled,
            contradiction=self.contradiction,
            limit_reached=limit_reached,
            hardest_strategy=self.hardest_strategy,
        )


def logical_solve(grid: Grid, max_steps: int = 500) -> LogicalResult:
    """Solve as far as the built-in deterministic human strategy stack can go."""

    state = LogicalState(grid)
    return state.run(max_steps=max_steps)


def _label_for_score(score: float) -> HumanDifficulty:
    if score <= 3.0:
        return "easy"
    if score <= 5.0:
        return "medium"
    if score <= 7.0:
        return "hard"
    return "expert"


def human_rate(grid: Grid, max_steps: int = 500) -> HumanRating:
    """Rate a puzzle by deterministic logical techniques rather than search work."""

    if not is_valid(grid):
        return HumanRating(
            version=HUMAN_DIFFICULTY_VERSION,
            score=10.0,
            label="expert",
            solved_logically=False,
            steps=0,
            placements=0,
            eliminations=0,
            hardest_strategy=None,
        )

    result = logical_solve(grid, max_steps=max_steps)
    placements = sum(step.get("type") == "place" for step in result.steps)
    eliminations = sum(step.get("type") == "eliminate" for step in result.steps)

    if not result.solved:
        return HumanRating(
            version=HUMAN_DIFFICULTY_VERSION,
            score=10.0,
            label="expert",
            solved_logically=False,
            steps=len(result.steps),
            placements=placements,
            eliminations=eliminations,
            hardest_strategy=result.hardest_strategy,
            contradiction=result.contradiction,
        )

    hardest = _STRATEGY_WEIGHT.get(result.hardest_strategy or "", 0.0)
    workload = min(math.log1p(len(result.steps)) / math.log(201.0), 1.0)
    elimination_load = min(eliminations / 20.0, 1.0)
    score = round(min(9.5, hardest + 0.8 * workload + 0.7 * elimination_load), 1)

    return HumanRating(
        version=HUMAN_DIFFICULTY_VERSION,
        score=score,
        label=_label_for_score(score),
        solved_logically=True,
        steps=len(result.steps),
        placements=placements,
        eliminations=eliminations,
        hardest_strategy=result.hardest_strategy,
        contradiction=False,
    )


__all__ = [
    "HUMAN_DIFFICULTY_VERSION",
    "HumanDifficulty",
    "HumanRating",
    "LogicalResult",
    "LogicalState",
    "human_rate",
    "logical_solve",
]
