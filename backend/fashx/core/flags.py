import logging
import time
from typing import Any

from sqlalchemy import select, update

from database.models.feature_flags import FeatureFlag
from fashx.core.database import get_db_session

logger = logging.getLogger("fashx.core.flags")

# Default in-memory cache with 30s TTL (Rule 9.10)
_FLAG_CACHE: dict[str, tuple[bool, float]] = {}
CACHE_TTL_SECONDS = 30.0

TRYON_ENABLED = "tryon_enabled"
MAINTENANCE_MODE = "maintenance_mode"
INGEST_ENABLED = "ingest_enabled"
SIGNUPS_OPEN = "signups_open"
END_SURVEY_OPEN = "end_survey_open"

_DEFAULTS = {
    TRYON_ENABLED: True,
    MAINTENANCE_MODE: False,
    INGEST_ENABLED: True,
    SIGNUPS_OPEN: False,
    END_SURVEY_OPEN: False,
}


def clear_flag_cache() -> None:
    """Clear in-memory flag cache (used in tests and after updates)."""
    _FLAG_CACHE.clear()


async def is_flag_enabled(
    flag_name: str,
    default: bool | None = None,
    session: Any | None = None,
) -> bool:
    """Return whether flag is enabled, checking 30s cache before querying DB."""
    now = time.monotonic()
    cached = _FLAG_CACHE.get(flag_name)
    if cached is not None:
        val, ts = cached
        if now - ts < CACHE_TTL_SECONDS:
            return val

    fallback = _DEFAULTS.get(flag_name, True) if default is None else default

    async def _query(s: Any) -> bool:
        stmt = select(FeatureFlag.enabled).where(FeatureFlag.name == flag_name)
        res = await s.execute(stmt)
        val = res.scalar_one_or_none()
        return val if val is not None else fallback

    try:
        if session is not None:
            enabled = await _query(session)
        else:
            async for s in get_db_session():
                enabled = await _query(s)
                break
    except Exception as e:
        logger.warning(f"Error querying feature flag {flag_name}, falling back to default {fallback}: {e}")
        enabled = fallback

    _FLAG_CACHE[flag_name] = (enabled, now)
    return enabled


async def set_flag(
    flag_name: str,
    enabled: bool,
    updated_by: str,
    reason: str,
    session: Any | None = None,
) -> None:
    """Update feature flag in DB, invalidate cache, and log audit event."""
    from datetime import UTC, datetime

    audit_logger = logging.getLogger("fashx.audit.flags")
    audit_logger.info(
        f"feature_flag_changed: {flag_name} set to {enabled} by {updated_by} - Reason: {reason}",
        extra={
            "flag_name": flag_name,
            "enabled": enabled,
            "updated_by": updated_by,
            "reason": reason,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )

    async def _update(s: Any) -> None:
        stmt = (
            update(FeatureFlag)
            .where(FeatureFlag.name == flag_name)
            .values(
                enabled=enabled,
                updated_by=updated_by,
                reason=reason,
                updated_at=datetime.now(UTC),
            )
        )
        res = await s.execute(stmt)
        if getattr(res, "rowcount", 0) == 0:
            # Insert if not present
            from sqlalchemy.dialects.postgresql import insert

            ins = (
                insert(FeatureFlag)
                .values(
                    name=flag_name,
                    enabled=enabled,
                    updated_by=updated_by,
                    reason=reason,
                    updated_at=datetime.now(UTC),
                )
                .on_conflict_do_update(
                    index_elements=["name"],
                    set_={
                        "enabled": enabled,
                        "updated_by": updated_by,
                        "reason": reason,
                        "updated_at": datetime.now(UTC),
                    },
                )
            )
            await s.execute(ins)
        await s.commit()

    if session is not None:
        await _update(session)
    else:
        async for s in get_db_session():
            await _update(s)
            break

    # Immediately invalidate and update cache
    _FLAG_CACHE[flag_name] = (enabled, time.monotonic())
