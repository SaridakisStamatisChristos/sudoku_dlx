"""A minimal stub of the :mod:`hypothesis` API used in the tests.

This project relies on Hypothesis for a couple of property-based tests.  The
evaluation environment, however, does not provide network access and therefore
cannot install the real dependency.  To keep the tests runnable we provide a
very small, deterministic implementation that mimics only the pieces of the
public API that our test-suite touches.  The goal is not to be feature-complete
but to offer a predictable drop-in replacement that covers:

* ``given`` decorator for generating combinations of examples.
* ``settings`` decorator and profile helpers used by ``tests/conftest.py``.
* ``Phase`` and ``HealthCheck`` enums referenced during profile registration.
* A ``strategies`` submodule offering ``sampled_from``, ``lists`` and ``text``.

The implementation favours simplicity and determinism: each strategy exposes a
small set of representative examples and ``given`` runs the wrapped test for
the cartesian product of all example values.  This still exercises the relevant
code paths while avoiding the complexity of Hypothesis' real engine.
"""

from __future__ import annotations

from enum import Enum
from functools import wraps
import inspect
from itertools import product
from typing import Any, Callable, Dict, List, Sequence, Tuple

from . import strategies as strategies

__all__ = [
    "HealthCheck",
    "Phase",
    "given",
    "settings",
    "strategies",
]


class HealthCheck(str, Enum):
    """Subset of health checks referenced in the test-suite."""

    too_slow = "too_slow"
    filter_too_much = "filter_too_much"
    data_too_large = "data_too_large"


class Phase(str, Enum):
    """Minimal enumeration mirroring Hypothesis' execution phases."""

    generate = "generate"
    shrink = "shrink"


class settings:
    """Compatibility shim for :func:`hypothesis.settings`.

    The decorator form simply records the provided keyword arguments on the
    wrapped function so Pytest can introspect them if required.  Profile
    registration/loading is implemented as light-weight dictionary storage.
    """

    _profiles: Dict[str, Dict[str, Any]] = {"default": {}}
    _active_profile: Dict[str, Any] = _profiles["default"].copy()

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        func._hypothesis_settings = self.kwargs  # type: ignore[attr-defined]
        return func

    @classmethod
    def register_profile(cls, name: str, **kwargs: Any) -> None:
        cls._profiles[name] = dict(kwargs)

    @classmethod
    def load_profile(cls, name: str) -> None:
        cls._active_profile = cls._profiles.get(name, cls._profiles["default"]).copy()

    @classmethod
    def get_active_profile(cls) -> Dict[str, Any]:
        return cls._active_profile


def given(*strategies_args: strategies.Strategy, **strategies_kwargs: strategies.Strategy) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Deterministic stand-in for :func:`hypothesis.given`.

    The decorator eagerly materialises example values from each strategy and
    invokes the wrapped test for every combination.  Keyword strategies are not
    currently required by the tests and therefore unsupported.
    """

    if strategies_kwargs:
        raise NotImplementedError("keyword strategies are not supported in this stub")

    example_lists: List[Sequence[Any]] = [s.examples() for s in strategies_args]

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not example_lists:
            return func

        example_product: List[Tuple[Any, ...]] = list(product(*example_lists))

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for example in example_product:
                func(*example)

        wrapper.__signature__ = inspect.Signature()  # type: ignore[attr-defined]

        return wrapper

    return decorator
