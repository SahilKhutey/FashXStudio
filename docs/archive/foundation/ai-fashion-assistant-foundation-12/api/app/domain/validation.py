from __future__ import annotations


def validate_confidence(value: float) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError("Confidence must be between 0 and 1")
    return value


def validate_budget(minimum: int | None, maximum: int | None) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("Minimum budget cannot exceed maximum budget")
