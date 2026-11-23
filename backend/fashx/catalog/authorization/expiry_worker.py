from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource
from database.models.catalog_auth import (
    CatalogPermissionStatus,
    CatalogSourcePermission,
    CatalogSourceStatus,
)


class ExpiryScanResult:
    def __init__(self, expired_sources: int, expired_permissions: int) -> None:
        self.expired_sources = expired_sources
        self.expired_permissions = expired_permissions


class CatalogExpiryWorker:
    @classmethod
    async def scan_and_expire(
        cls, session: AsyncSession, now: datetime | None = None
    ) -> ExpiryScanResult:
        if now is None:
            now = datetime.now(UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        # 1. Expire sources whose expires_at is past
        source_stmt = (
            update(CatalogSource)
            .where(
                CatalogSource.expires_at.is_not(None),
                CatalogSource.expires_at < now,
                CatalogSource.source_status == CatalogSourceStatus.ACTIVE.value,
            )
            .values(
                source_status=CatalogSourceStatus.EXPIRED.value,
                status="suspended",
                rights_display=False,
                rights_tryon=False,
            )
        )
        source_res = await session.execute(source_stmt)
        expired_sources = source_res.rowcount

        # 2. Expire permissions whose expires_at is past
        perm_stmt = (
            update(CatalogSourcePermission)
            .where(
                CatalogSourcePermission.expires_at.is_not(None),
                CatalogSourcePermission.expires_at < now,
                CatalogSourcePermission.permission_status == CatalogPermissionStatus.GRANTED.value,
                CatalogSourcePermission.revoked_at.is_(None),
            )
            .values(
                permission_status=CatalogPermissionStatus.EXPIRED.value,
            )
        )
        perm_res = await session.execute(perm_stmt)
        expired_perms = perm_res.rowcount

        await session.flush()
        return ExpiryScanResult(
            expired_sources=expired_sources,
            expired_permissions=expired_perms,
        )
