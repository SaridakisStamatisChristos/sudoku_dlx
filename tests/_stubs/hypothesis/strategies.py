"""Deterministic stand-ins for a tiny subset of Hypothesis strategies."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Sequence
__all__ = ["Strategy", "sampled_from", "lists", "text"]
class Strategy:
    def examples(self) -> Sequence[object]:
        raise NotImplementedError
@dataclass
class SampledFromStrategy(Strategy):
    values: Sequence[object]
    def __post_init__(self) -> None:
        if not self.values:
            self.values = [None]
    def examples(self) -> Sequence[object]:
        unique: List[object] = []
        for candidate in (self.values[0], self.values[-1]):
            if candidate not in unique:
                unique.append(candidate)
        midpoint = self.values[len(self.values) // 2]
        if midpoint not in unique:
            unique.append(midpoint)
        return tuple(unique)
    def cycle(self, length: int, *, reverse: bool = False, offset: int = 0) -> List[object]:
        items = list(self.values[::-1] if reverse else self.values) or [None]
        return [items[(i + offset) % len(items)] for i in range(length)]
@dataclass
class ListStrategy(Strategy):
    inner: Strategy
    min_size: int
    max_size: int
    def examples(self) -> Sequence[object]:
        length = min(max(self.min_size, 0), max(self.max_size, 0))
        cycle = getattr(self.inner, "cycle", None)
        if callable(cycle):
            base = cycle(length)
            rotated = cycle(length, offset=1) if length else []
            reversed_cycle = cycle(length, reverse=True) if length else []
        else:
            base_values = list(self.inner.examples()) or [None]
            base = [(base_values[i % len(base_values)]) for i in range(length)]
            rotated = base[::-1]
            reversed_cycle = base_values[:length]
        examples: List[List[object]] = [list(base)]
        if rotated and rotated != base:
            examples.append(list(rotated))
        if reversed_cycle and reversed_cycle not in examples:
            examples.append(list(reversed_cycle))
        if self.max_size > self.min_size:
            alt_length = self.max_size
            if callable(cycle):
                alt = cycle(alt_length, offset=2)
            else:
                base_values = list(self.inner.examples()) or [None]
                alt = [(base_values[i % len(base_values)]) for i in range(alt_length)]
            if alt:
                examples.append(list(alt))
        return tuple(examples)
@dataclass
class TextStrategy(Strategy):
    alphabet: Strategy
    min_size: int
    max_size: int
    def examples(self) -> Sequence[object]:
        chars = [str(c) for c in self.alphabet.examples() if str(c)] or [""]
        examples: List[str] = [""]
        if self.min_size > 0:
            repeat_count = min(max(self.min_size, 1), self.max_size)
            examples.append(chars[0] * repeat_count)
        if len(chars) > 1:
            joined = "".join(chars)
            examples.append(joined[: self.max_size])
        return tuple(examples)
def sampled_from(values: Iterable[object]) -> SampledFromStrategy:
    return SampledFromStrategy(tuple(values))
def lists(inner: Strategy, *, min_size: int, max_size: int) -> ListStrategy:
    return ListStrategy(inner=inner, min_size=min_size, max_size=max_size)
def text(*, alphabet: Strategy, min_size: int, max_size: int) -> TextStrategy:
    return TextStrategy(alphabet=alphabet, min_size=min_size, max_size=max_size)
