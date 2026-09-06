from __future__ import annotations

from .api import (
    Grid,
    SolveResult,
    Stats,
    analyze,
    build_reveal_trace,
    count_solutions,
    from_string,
    is_valid,
    is_well_formed,
    solve,
    to_string,
)
from .canonical import canonical_form
from .crosscheck import cnf_dimacs_lines, sat_solve
from .explain import explain
from .formats import detect_format, read_grids, write_grids
from .generate import GenerationResult, generate, generate_rated, generate_result
from .logic import (
    HUMAN_DIFFICULTY_VERSION,
    HumanDifficulty,
    HumanRating,
    LogicalResult,
    LogicalState,
    human_rate,
    logical_solve,
)
from .rating import DIFFICULTY_VERSION, rate
from .solver import (
    SOLVER,
    from_string as legacy_from_string,
    generate_minimal,
    grid_clues,
    hardness_estimate,
    is_minimal,
    print_grid,
    set_seed,
    to_string as legacy_to_string,
    validate_grid,
)

__all__ = [
    "Grid",
    "Stats",
    "SolveResult",
    "from_string",
    "to_string",
    "build_reveal_trace",
    "is_well_formed",
    "is_valid",
    "solve",
    "analyze",
    "count_solutions",
    "explain",
    "logical_solve",
    "LogicalState",
    "LogicalResult",
    "human_rate",
    "HumanRating",
    "HumanDifficulty",
    "HUMAN_DIFFICULTY_VERSION",
    "rate",
    "DIFFICULTY_VERSION",
    "canonical_form",
    "generate",
    "generate_result",
    "generate_rated",
    "GenerationResult",
    "sat_solve",
    "cnf_dimacs_lines",
    "read_grids",
    "write_grids",
    "detect_format",
    "SOLVER",
    "generate_minimal",
    "is_minimal",
    "print_grid",
    "grid_clues",
    "set_seed",
    "validate_grid",
    "hardness_estimate",
    "legacy_from_string",
    "legacy_to_string",
]

__version__ = "1.1.0"
