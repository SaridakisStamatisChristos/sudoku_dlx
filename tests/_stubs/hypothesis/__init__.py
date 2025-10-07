"""Minimal Hypothesis stub used only when the real package is unavailable."""
from __future__ import annotations
from enum import Enum
from functools import wraps
import inspect
from itertools import product
from typing import Any, Callable, Dict, List, Sequence, Tuple
from . import strategies as strategies
__all__ = ["HealthCheck","Phase","given","settings","strategies"]
class HealthCheck(str, Enum):
    too_slow = "too_slow"
    filter_too_much = "filter_too_much"
    data_too_large = "data_too_large"
class Phase(str, Enum):
    generate = "generate"
    shrink = "shrink"
class settings:
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

def given(*strategies_args: strategies.Strategy, **strategies_kwargs: strategies.Strategy):
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
