from __future__ import annotations

from .api import (
    Grid,
    SolveResult,
    Stats,
    count_solutions,
    from_string,
    is_valid,
    solve,
    to_string,
)
from .canonical import canonical_form
from .generate import generate
from .rating import rate
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
    "is_valid",
    "solve",
    "count_solutions",
    "rate",
    "canonical_form",
    "generate",
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

__version__ = "0.1.0"
