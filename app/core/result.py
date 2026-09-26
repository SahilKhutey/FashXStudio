from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .errors import CoreError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Success(Generic[T]):
    value: T


@dataclass(frozen=True, slots=True)
class Failure:
    error: CoreError


Result = Success[T] | Failure
