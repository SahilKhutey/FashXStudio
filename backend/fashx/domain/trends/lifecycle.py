from app.core.errors import ConflictError

from .enums import TrendStatus

_ALLOWED_TRANSITIONS: dict[TrendStatus, set[TrendStatus]] = {
    TrendStatus.DRAFT: {
        TrendStatus.ACTIVE,
        TrendStatus.ARCHIVED,
    },
    TrendStatus.ACTIVE: {
        TrendStatus.EXPIRED,
        TrendStatus.ARCHIVED,
    },
    TrendStatus.EXPIRED: {
        TrendStatus.ARCHIVED,
    },
    TrendStatus.ARCHIVED: set(),
}


def validate_trend_transition(
    current: TrendStatus,
    target: TrendStatus,
) -> None:
    if target not in _ALLOWED_TRANSITIONS.get(
        current,
        set(),
    ):
        raise ConflictError(
            f"Invalid trend transition: {current} -> {target}"
        )
