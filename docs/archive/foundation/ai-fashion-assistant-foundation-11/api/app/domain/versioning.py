from __future__ import annotations


def next_version(current: int) -> int:
    if current < 1:
        raise ValueError("Version must be positive")
    return current + 1
