from __future__ import annotations

from .api import (
    Grid,
    SolveResult,
    Stats,
    count_solutions,
    from_string,
    is_valid,
    analyze,
    solve,
    to_string,
    build_reveal_trace,
)
from .explain import explain
from .canonical import canonical_form
from .generate import generate
from .rating import rate
from .crosscheck import sat_solve
from .solver import (
    SOLVER,
    generate_minimal,
    grid_clues,
    hardness_estimate,
    is_minimal,
    print_grid,
    set_seed,
    to_string as legacy_to_string,
    from_string as legacy_from_string,
    validate_grid,
)

__all__ = [
    "Grid",
    "Stats",
    "SolveResult",
    "from_string",
    "to_string",
    "build_reveal_trace",
    "is_valid",
    "solve",
    "analyze",
    "count_solutions",
    "explain",
    "rate",
    "canonical_form",
    "generate",
    "sat_solve",
    # Legacy exports
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

__version__ = "0.2.0"
