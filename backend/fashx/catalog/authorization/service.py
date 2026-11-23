from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_auth import (
    CatalogAuthorizationEvidence,
    CatalogPermissionStatus,
    CatalogSourcePermission,
    CatalogTakedownRequest,
)
from fashx.catalog.authorization.audit import log_authorization_decision
from fashx.catalog.authorization.evaluator import CatalogAuthorizationEvaluator
from fashx.catalog.authorization.repository import (
    AuthorizationEvidenceRepository,
    CatalogAuthorizationDecisionRepository,
    CatalogPermissionRepository,
)
from fashx.catalog.authorization.schemas import (
    AuthorizationContext,
    AuthorizationDecisionResponse,
    EvidenceCreate,
    PermissionCreate,
)
from fashx.catalog.errors import SourceNotFoundError


class CatalogAuthorizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.perm_repo = CatalogPermissionRepository(session)
        self.evidence_repo = AuthorizationEvidenceRepository(session)
        self.decision_repo = CatalogAuthorizationDecisionRepository(session)

    async def add_evidence(self, payload: EvidenceCreate) -> CatalogAuthorizationEvidence:
        # Check source exists
        source_res = await self.session.execute(
            select(CatalogSource).where(CatalogSource.id == payload.source_id)
        )
        source = source_res.scalar_one_or_none()
        if not source:
            raise SourceNotFoundError(payload.source_id)

        evidence = CatalogAuthorizationEvidence(
            source_id=payload.source_id,
            evidence_type=payload.evidence_type,
            document_reference=payload.document_reference,
            document_sha256=payload.document_sha256,
            agreement_reference=payload.agreement_reference,
            agreement_version=payload.agreement_version,
            granted_by_name=payload.granted_by_name,
            granted_by_role=payload.granted_by_role,
            verified_by=payload.verified_by,
            effective_at=payload.effective_at,
            expires_at=payload.expires_at,
            verification_status=payload.verification_status.value,
        )
        return await self.evidence_repo.create(evidence)

    async def grant_permission(self, payload: PermissionCreate) -> CatalogSourcePermission:
        # Check source exists
        source_res = await self.session.execute(
            select(CatalogSource).where(CatalogSource.id == payload.source_id)
        )
        source = source_res.scalar_one_or_none()
        if not source:
            raise SourceNotFoundError(payload.source_id)

        effective_at = payload.effective_at or datetime.now(UTC)
        permission = CatalogSourcePermission(
            source_id=payload.source_id,
            permission_code=payload.permission_code.value,
            permission_status=CatalogPermissionStatus.GRANTED.value,
            granted_by=payload.granted_by,
            evidence_id=payload.evidence_id,
            scope_categories=payload.scope_categories,
            scope_markets=payload.scope_markets,
            processor_restrictions=payload.processor_restrictions,
            storage_limit_days=payload.storage_limit_days,
            effective_at=effective_at,
            expires_at=payload.expires_at,
        )
        return await self.perm_repo.create(permission)

    async def revoke_permission(self, permission_id: UUID, reason: str) -> CatalogSourcePermission:
        perm = await self.perm_repo.get_by_id(permission_id)
        if not perm:
            raise ValueError(f"Permission '{permission_id}' not found.")

        perm.permission_status = CatalogPermissionStatus.REVOKED.value
        perm.revoked_at = datetime.now(UTC)
        return await self.perm_repo.update(perm)

    async def evaluate(
        self, context: AuthorizationContext, now: datetime | None = None
    ) -> AuthorizationDecisionResponse:
        if now is None:
            now = datetime.now(UTC)

        # 1. Load source
        source_res = await self.session.execute(
            select(CatalogSource).where(CatalogSource.id == context.source_id)
        )
        source = source_res.scalar_one_or_none()

        # 2. Load merchant
        merchant = None
        if source and source.merchant_id:
            m_res = await self.session.execute(
                select(Merchant).where(Merchant.id == source.merchant_id)
            )
            merchant = m_res.scalar_one_or_none()

        # 3. Load evidence
        evidence_list: Sequence[CatalogAuthorizationEvidence] = []
        if source:
            ev_res = await self.session.execute(
                select(CatalogAuthorizationEvidence).where(
                    CatalogAuthorizationEvidence.source_id == source.id
                )
            )
            evidence_list = ev_res.scalars().all()

        # 4. Load permissions
        permissions_list: Sequence[CatalogSourcePermission] = []
        if source:
            p_res = await self.session.execute(
                select(CatalogSourcePermission).where(
                    CatalogSourcePermission.source_id == source.id
                )
            )
            permissions_list = p_res.scalars().all()

        # 5. Load takedowns
        takedowns_list: Sequence[CatalogTakedownRequest] = []
        if source:
            t_res = await self.session.execute(
                select(CatalogTakedownRequest).where(CatalogTakedownRequest.source_id == source.id)
            )
            takedowns_list = t_res.scalars().all()

        result = CatalogAuthorizationEvaluator.evaluate(
            context=context,
            source=source,
            merchant=merchant,
            evidence_list=evidence_list,
            permissions_list=permissions_list,
            active_takedowns=takedowns_list,
            now=now,
        )

        # Record audit entry in catalog_authorization_decisions
        await log_authorization_decision(
            session=self.session,
            context=context,
            result=result,
            evaluated_at=now,
        )

        return AuthorizationDecisionResponse(
            decision=result.decision,
            reason_code=result.reason_code,
            source_id=context.source_id,
            product_id=context.product_id,
            operation=context.operation,
            permission_id=result.permission_id,
            evaluated_at=now,
        )

    async def list_permissions(self, source_id: UUID) -> Sequence[CatalogSourcePermission]:
        return await self.perm_repo.list_by_source(source_id)

    async def list_evidence(self, source_id: UUID) -> Sequence[CatalogAuthorizationEvidence]:
        return await self.evidence_repo.list_by_source(source_id)
