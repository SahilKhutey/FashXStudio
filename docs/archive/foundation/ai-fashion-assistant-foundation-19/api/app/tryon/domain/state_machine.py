from __future__ import annotations

from schemas.common.enums import TryOnStatus


_ALLOWED: dict[str, set[str]] = {
    TryOnStatus.QUEUED.value: {TryOnStatus.VALIDATING.value, TryOnStatus.CANCELLED.value},
    TryOnStatus.VALIDATING.value: {TryOnStatus.PREPROCESSING.value, TryOnStatus.FAILED.value, TryOnStatus.CANCELLED.value},
    TryOnStatus.PREPROCESSING.value: {TryOnStatus.INFERENCE.value, TryOnStatus.FAILED.value, TryOnStatus.CANCELLED.value},
    TryOnStatus.INFERENCE.value: {TryOnStatus.POSTPROCESSING.value, TryOnStatus.FAILED.value, TryOnStatus.CANCELLED.value},
    TryOnStatus.POSTPROCESSING.value: {TryOnStatus.QUALITY_CHECK.value, TryOnStatus.FAILED.value, TryOnStatus.CANCELLED.value},
    TryOnStatus.QUALITY_CHECK.value: {TryOnStatus.COMPLETED.value, TryOnStatus.FAILED.value},
    TryOnStatus.COMPLETED.value: set(),
    TryOnStatus.FAILED.value: set(),
    TryOnStatus.CANCELLED.value: set(),
}


def can_transition(current: str, target: str) -> bool:
    return target in _ALLOWED.get(current, set())
