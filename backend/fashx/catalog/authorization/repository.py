from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_auth import (
    CatalogAuthorizationDecision,
    CatalogAuthorizationEvidence,
    CatalogSourcePermission,
)


class CatalogPermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, permission: CatalogSourcePermission) -> CatalogSourcePermission:
        self.session.add(permission)
        await self.session.flush()
        return permission

    async def get_by_id(self, permission_id: UUID) -> CatalogSourcePermission | None:
        stmt = select(CatalogSourcePermission).where(CatalogSourcePermission.id == permission_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_source(self, source_id: UUID) -> Sequence[CatalogSourcePermission]:
        stmt = (
            select(CatalogSourcePermission)
            .where(CatalogSourcePermission.source_id == source_id)
            .order_by(CatalogSourcePermission.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def update(self, permission: CatalogSourcePermission) -> CatalogSourcePermission:
        await self.session.flush()
        return permission


class AuthorizationEvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, evidence: CatalogAuthorizationEvidence) -> CatalogAuthorizationEvidence:
        self.session.add(evidence)
        await self.session.flush()
        return evidence

    async def get_by_id(self, evidence_id: UUID) -> CatalogAuthorizationEvidence | None:
        stmt = select(CatalogAuthorizationEvidence).where(
            CatalogAuthorizationEvidence.id == evidence_id
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_source(self, source_id: UUID) -> Sequence[CatalogAuthorizationEvidence]:
        stmt = (
            select(CatalogAuthorizationEvidence)
            .where(CatalogAuthorizationEvidence.source_id == source_id)
            .order_by(CatalogAuthorizationEvidence.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def update(self, evidence: CatalogAuthorizationEvidence) -> CatalogAuthorizationEvidence:
        await self.session.flush()
        return evidence


class CatalogAuthorizationDecisionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, decision: CatalogAuthorizationDecision) -> CatalogAuthorizationDecision:
        self.session.add(decision)
        await self.session.flush()
        return decision

    async def list_by_source(
        self, source_id: UUID, limit: int = 50
    ) -> Sequence[CatalogAuthorizationDecision]:
        stmt = (
            select(CatalogAuthorizationDecision)
            .where(CatalogAuthorizationDecision.source_id == source_id)
            .order_by(CatalogAuthorizationDecision.evaluated_at.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()
