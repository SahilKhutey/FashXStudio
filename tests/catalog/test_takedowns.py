from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import MerchantProduct
from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogSourceStatus,
    EvidenceVerificationStatus,
    MerchantVerificationStatus,
    TakedownReasonCode,
    TakedownStatus,
)
from fashx.catalog.authorization.schemas import (
    AuthorizationContext,
    EvidenceCreate,
    PermissionCreate,
)
from fashx.catalog.authorization.service import CatalogAuthorizationService
from fashx.catalog.merchants.schemas import MerchantCreate, MerchantVerificationRequest
from fashx.catalog.merchants.service import MerchantService
from fashx.catalog.sources.schemas import SourceCreate, SourceStatusUpdate
from fashx.catalog.sources.service import CatalogSourceService
from fashx.catalog.takedowns.schemas import (
    TakedownRequestCreate,
    TakedownResolutionRequest,
)
from fashx.catalog.takedowns.service import CatalogTakedownService
from fashx.catalog.takedowns.worker import TakedownAsyncWorker


async def _create_active_source_with_permissions(
    session: AsyncSession,
    slug: str,
) -> tuple[any, any, any]:
    m_service = MerchantService(session)
    s_service = CatalogSourceService(session)
    auth_service = CatalogAuthorizationService(session)

    merchant = await m_service.register_merchant(
        MerchantCreate(name=f"Merchant-{slug}", legal_name=f"Legal-{slug} Ltd")
    )
    await m_service.verify_merchant(
        merchant.id,
        MerchantVerificationRequest(
            verification_status=MerchantVerificationStatus.VERIFIED,
            reason="Verified",
        ),
    )

    source = await s_service.register_source(
        SourceCreate(merchant_id=merchant.id, slug=slug, name=f"Source-{slug}")
    )
    await s_service.update_source_status(
        source.id,
        SourceStatusUpdate(target_status=CatalogSourceStatus.APPROVED, reason="Approved"),
    )

    ev = await auth_service.add_evidence(
        EvidenceCreate(
            source_id=source.id,
            document_reference=f"docs/{slug}.pdf",
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
    )
    await auth_service.grant_permission(
        PermissionCreate(
            source_id=source.id,
            permission_code=CatalogPermissionCode.PRODUCT_DATA_READ,
            granted_by="Legal",
            evidence_id=ev.id,
        )
    )
    await auth_service.grant_permission(
        PermissionCreate(
            source_id=source.id,
            permission_code=CatalogPermissionCode.IMAGE_DISPLAY,
            granted_by="Legal",
            evidence_id=ev.id,
        )
    )
    await s_service.update_source_status(
        source.id,
        SourceStatusUpdate(target_status=CatalogSourceStatus.ACTIVE, reason="Active"),
    )
    await session.commit()
    return merchant, source, auth_service


@pytest.mark.asyncio
async def test_cat_take_001_immediate_suspension_on_takedown(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-001: Immediate suspension upon takedown receipt."""
    async with session_factory() as session:
        merchant, source, _ = await _create_active_source_with_permissions(session, "take-001")
        t_service = CatalogTakedownService(session)
        s_service = CatalogSourceService(session)

        takedown = await t_service.initiate_takedown(
            TakedownRequestCreate(
                source_id=source.id,
                reason_code=TakedownReasonCode.IMAGE_RIGHTS_DISPUTE,
                requested_by="Photographer Rights Agency",
                request_reference="IP-2026-981",
            )
        )
        await session.commit()

        assert takedown.id is not None
        assert takedown.status == TakedownStatus.SUSPENDED.value

        refreshed_source = await s_service.get_source(source.id)
        assert refreshed_source.source_status == CatalogSourceStatus.SUSPENDED.value
        assert refreshed_source.status == "suspended"
        assert refreshed_source.rights_display is False


@pytest.mark.asyncio
async def test_cat_take_002_takedown_reason_codes_recorded(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-002: Takedown reason codes recorded accurately."""
    async with session_factory() as session:
        _, source, _ = await _create_active_source_with_permissions(session, "take-002")
        t_service = CatalogTakedownService(session)

        reasons = [
            TakedownReasonCode.MERCHANT_REQUEST,
            TakedownReasonCode.LICENSE_EXPIRED,
            TakedownReasonCode.CREDENTIAL_COMPROMISE,
        ]
        for r in reasons:
            td = await t_service.initiate_takedown(
                TakedownRequestCreate(
                    source_id=source.id,
                    reason_code=r,
                    requested_by="Security Team",
                )
            )
            assert td.reason_code == r.value


@pytest.mark.asyncio
async def test_cat_take_003_evaluator_denies_all_during_active_takedown(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-003: Authorization engine denies all operations during active takedown."""
    async with session_factory() as session:
        _, source, auth_service = await _create_active_source_with_permissions(session, "take-003")
        t_service = CatalogTakedownService(session)

        # Before takedown -> ALLOW
        pre = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert pre.decision == "ALLOW"

        # Initiate takedown
        await t_service.initiate_takedown(
            TakedownRequestCreate(
                source_id=source.id,
                reason_code=TakedownReasonCode.LEGAL_REQUEST,
                requested_by="Legal Counsel",
            )
        )
        await session.commit()

        # After takedown -> DENY
        post = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert post.decision == "DENY"
        assert post.reason_code in ("DENY_SOURCE_SUSPENDED", "DENY_SOURCE_TAKEDOWN_ACTIVE")


@pytest.mark.asyncio
async def test_cat_take_004_multi_source_isolation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-004: Multi-source isolation (takedown on source A does not suspend source B of same merchant)."""
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)
        auth_service = CatalogAuthorizationService(session)
        t_service = CatalogTakedownService(session)

        merchant = await m_service.register_merchant(
            MerchantCreate(name="MultiBrand", legal_name="MultiBrand Global Ltd")
        )
        await m_service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.VERIFIED,
                reason="Verified",
            ),
        )

        # Source A
        s_a = await s_service.register_source(
            SourceCreate(merchant_id=merchant.id, slug="src-a", name="Source A")
        )
        await s_service.update_source_status(
            s_a.id,
            SourceStatusUpdate(target_status=CatalogSourceStatus.APPROVED, reason="Approved"),
        )
        ev_a = await auth_service.add_evidence(
            EvidenceCreate(source_id=s_a.id, document_reference="docs/a.pdf")
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=s_a.id,
                permission_code=CatalogPermissionCode.PRODUCT_DATA_READ,
                granted_by="Legal",
                evidence_id=ev_a.id,
            )
        )
        await s_service.update_source_status(
            s_a.id,
            SourceStatusUpdate(target_status=CatalogSourceStatus.ACTIVE, reason="Active"),
        )

        # Source B
        s_b = await s_service.register_source(
            SourceCreate(merchant_id=merchant.id, slug="src-b", name="Source B")
        )
        await s_service.update_source_status(
            s_b.id,
            SourceStatusUpdate(target_status=CatalogSourceStatus.APPROVED, reason="Approved"),
        )
        ev_b = await auth_service.add_evidence(
            EvidenceCreate(source_id=s_b.id, document_reference="docs/b.pdf")
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=s_b.id,
                permission_code=CatalogPermissionCode.PRODUCT_DATA_READ,
                granted_by="Legal",
                evidence_id=ev_b.id,
            )
        )
        await s_service.update_source_status(
            s_b.id,
            SourceStatusUpdate(target_status=CatalogSourceStatus.ACTIVE, reason="Active"),
        )
        await session.commit()

        # Takedown only Source A
        await t_service.initiate_takedown(
            TakedownRequestCreate(
                source_id=s_a.id,
                reason_code=TakedownReasonCode.IMAGE_RIGHTS_DISPUTE,
                requested_by="Agency",
            )
        )
        await session.commit()

        # Source A is suspended & denied
        refreshed_a = await s_service.get_source(s_a.id)
        assert refreshed_a.source_status == CatalogSourceStatus.SUSPENDED.value
        res_a = await auth_service.evaluate(
            AuthorizationContext(
                source_id=s_a.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert res_a.decision == "DENY"

        # Source B remains active & allowed!
        refreshed_b = await s_service.get_source(s_b.id)
        assert refreshed_b.source_status == CatalogSourceStatus.ACTIVE.value
        res_b = await auth_service.evaluate(
            AuthorizationContext(
                source_id=s_b.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert res_b.decision == "ALLOW"


@pytest.mark.asyncio
async def test_cat_take_005_merchant_suspension_cascades_to_all_sources(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-005: Merchant suspension suspends all child sources."""
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)
        auth_service = CatalogAuthorizationService(session)

        merchant = await m_service.register_merchant(
            MerchantCreate(name="CascadeBrand", legal_name="Cascade Brand Corp")
        )
        await m_service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.VERIFIED,
                reason="Verified",
            ),
        )

        # Create two active sources
        s1 = await s_service.register_source(
            SourceCreate(merchant_id=merchant.id, slug="casc-1", name="Casc 1")
        )
        s2 = await s_service.register_source(
            SourceCreate(merchant_id=merchant.id, slug="casc-2", name="Casc 2")
        )
        for s in (s1, s2):
            await s_service.update_source_status(
                s.id,
                SourceStatusUpdate(target_status=CatalogSourceStatus.APPROVED, reason="Approved"),
            )
            ev = await auth_service.add_evidence(
                EvidenceCreate(source_id=s.id, document_reference="docs/c.pdf")
            )
            await auth_service.grant_permission(
                PermissionCreate(
                    source_id=s.id,
                    permission_code=CatalogPermissionCode.PRODUCT_DATA_READ,
                    granted_by="Legal",
                    evidence_id=ev.id,
                )
            )
            await s_service.update_source_status(
                s.id, SourceStatusUpdate(target_status=CatalogSourceStatus.ACTIVE, reason="Active")
            )
        await session.commit()

        # Suspend Merchant
        await m_service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.SUSPENDED,
                reason="Regulatory suspension order",
            ),
        )
        await session.commit()

        # Both sources must now be SUSPENDED
        refreshed_s1 = await s_service.get_source(s1.id)
        refreshed_s2 = await s_service.get_source(s2.id)
        assert refreshed_s1.source_status == CatalogSourceStatus.SUSPENDED.value
        assert refreshed_s2.source_status == CatalogSourceStatus.SUSPENDED.value


@pytest.mark.asyncio
async def test_cat_take_006_takedown_triage_and_assignment(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-006: Takedown triage and assignment to reviewer."""
    async with session_factory() as session:
        _, source, _ = await _create_active_source_with_permissions(session, "take-006")
        t_service = CatalogTakedownService(session)

        takedown = await t_service.initiate_takedown(
            TakedownRequestCreate(
                source_id=source.id,
                reason_code=TakedownReasonCode.DATA_RIGHTS_DISPUTE,
                requested_by="Brand Counsel",
            )
        )
        reviewer_id = uuid4()
        triaged = await t_service.triage_takedown(
            takedown.id,
            reviewer_id=reviewer_id,
            notes="Assigned to senior catalog reviewer for license verification.",
        )
        await session.commit()

        assert triaged.status == TakedownStatus.PROCESSING.value
        assert triaged.assigned_reviewer == reviewer_id
        assert "senior catalog reviewer" in (triaged.resolution_notes or "")


@pytest.mark.asyncio
async def test_cat_take_007_takedown_resolution_and_completion(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-007: Takedown resolution and completion workflow."""
    async with session_factory() as session:
        _, source, _ = await _create_active_source_with_permissions(session, "take-007")
        t_service = CatalogTakedownService(session)

        takedown = await t_service.initiate_takedown(
            TakedownRequestCreate(
                source_id=source.id,
                reason_code=TakedownReasonCode.INCORRECT_PRODUCT_DATA,
                requested_by="QA Team",
            )
        )
        reviewer = uuid4()
        resolved = await t_service.resolve_takedown(
            takedown.id,
            TakedownResolutionRequest(
                resolution_notes="Incorrect pricing data purged and upstream corrected.",
                reviewer_id=reviewer,
            ),
        )
        await session.commit()

        assert resolved.status == TakedownStatus.COMPLETED.value
        assert resolved.completed_at is not None
        assert resolved.assigned_reviewer == reviewer


@pytest.mark.asyncio
async def test_cat_take_008_resume_source_post_resolution(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-008: Resume source post-resolution requires active permissions and verified evidence."""
    async with session_factory() as session:
        _, source, auth_service = await _create_active_source_with_permissions(session, "take-008")
        t_service = CatalogTakedownService(session)
        s_service = CatalogSourceService(session)

        # 1. Takedown
        td = await t_service.initiate_takedown(
            TakedownRequestCreate(
                source_id=source.id,
                reason_code=TakedownReasonCode.PROVIDER_TERMINATION,
                requested_by="Admin",
            )
        )
        # 2. Resolve takedown
        await t_service.resolve_takedown(
            td.id,
            TakedownResolutionRequest(
                resolution_notes="Provider agreement renegotiated and re-signed.",
                reviewer_id=uuid4(),
            ),
        )
        await session.commit()

        # 3. Resume source
        resumed = await s_service.resume_source(source.id, reason="Agreement resolved and valid.")
        await session.commit()

        assert resumed.source_status == CatalogSourceStatus.ACTIVE.value
        assert resumed.rights_display is True

        # Now authorization engine allows requests again
        res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert res.decision == "ALLOW"


@pytest.mark.asyncio
async def test_cat_take_009_background_worker_unpublishes_affected_products(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-009: Background worker unpublishes affected products."""
    async with session_factory() as session:
        merchant, source, _ = await _create_active_source_with_permissions(session, "take-009")
        t_service = CatalogTakedownService(session)

        # Create dummy merchant products for this source
        p1 = MerchantProduct(
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="SKU-TAKE-1",
            title="Product 1",
            source_url="https://example.com/1",
            status="active",
        )
        p2 = MerchantProduct(
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="SKU-TAKE-2",
            title="Product 2",
            source_url="https://example.com/2",
            status="active",
        )
        session.add_all([p1, p2])
        await session.flush()
        await session.commit()

        # Takedown
        td = await t_service.initiate_takedown(
            TakedownRequestCreate(
                source_id=source.id,
                reason_code=TakedownReasonCode.MERCHANT_REQUEST,
                requested_by="Merchant Rep",
            )
        )
        await session.commit()

        # Worker unpublishes
        affected = await TakedownAsyncWorker.process_unpublishing(
            session=session, takedown_id=td.id, source_id=source.id
        )
        await session.commit()

        assert affected == 2

        # Check takedown record count
        refreshed_td = await t_service.get_takedown(td.id)
        assert refreshed_td.affected_product_count == 2


@pytest.mark.asyncio
async def test_cat_take_010_emergency_takedown_authorization_and_audit(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-TAKE-010: Emergency takedown authorization denial & audit verification."""
    from fashx.catalog.errors import PermissionDeniedError
    from fashx.catalog.ingestion.authorization_guard import CatalogAuthorizationGuard

    async with session_factory() as session:
        _, source, _ = await _create_active_source_with_permissions(session, "take-010")
        t_service = CatalogTakedownService(session)
        guard = CatalogAuthorizationGuard(session)

        # Before takedown, guard succeeds
        pre_dec = await guard.guard_product_read(source.id)
        assert pre_dec.decision == "ALLOW"

        # Emergency takedown for security incident
        await t_service.initiate_takedown(
            TakedownRequestCreate(
                source_id=source.id,
                reason_code=TakedownReasonCode.SECURITY_INCIDENT,
                requested_by="CISO Office",
                request_reference="SEC-INC-991",
            )
        )
        await session.commit()

        # Ingestion guard must immediately raise PermissionDeniedError
        with pytest.raises(PermissionDeniedError) as exc:
            await guard.guard_product_read(source.id)
        assert exc.value.status_code == 403
        assert exc.value.code in ("DENY_SOURCE_SUSPENDED", "DENY_SOURCE_TAKEDOWN_ACTIVE")
