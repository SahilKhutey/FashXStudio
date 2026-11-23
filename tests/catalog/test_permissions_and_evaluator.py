from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog_auth import (
    CatalogAuthorizationDecision,
    CatalogPermissionCode,
    CatalogSourceStatus,
    EvidenceVerificationStatus,
    MerchantVerificationStatus,
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


async def _setup_verified_merchant_and_active_source(
    session: AsyncSession,
    slug: str,
    categories: list[str] | None = None,
    markets: list[str] | None = None,
) -> tuple[CatalogAuthorizationService, CatalogSourceService, any, any]:
    m_service = MerchantService(session)
    s_service = CatalogSourceService(session)
    auth_service = CatalogAuthorizationService(session)

    merchant = await m_service.register_merchant(
        MerchantCreate(
            name=f"Merchant-{slug}",
            legal_name=f"Legal Entity {slug} Private Limited",
        )
    )
    await m_service.verify_merchant(
        merchant.id,
        MerchantVerificationRequest(
            verification_status=MerchantVerificationStatus.VERIFIED,
            reason="Verified corporate docs",
        ),
    )

    source = await s_service.register_source(
        SourceCreate(
            merchant_id=merchant.id,
            slug=slug,
            name=f"Source {slug}",
            category_codes=categories or ["apparel"],
            market_codes=markets or ["IN"],
        )
    )
    await s_service.update_source_status(
        source.id,
        SourceStatusUpdate(target_status=CatalogSourceStatus.APPROVED, reason="Approved"),
    )

    ev = await auth_service.add_evidence(
        EvidenceCreate(
            source_id=source.id,
            document_reference=f"contracts/{slug}.pdf",
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
    )

    # Initial permission to allow source activation
    await auth_service.grant_permission(
        PermissionCreate(
            source_id=source.id,
            permission_code=CatalogPermissionCode.PRODUCT_DATA_READ,
            granted_by="Counsel",
            evidence_id=ev.id,
        )
    )

    await s_service.update_source_status(
        source.id,
        SourceStatusUpdate(target_status=CatalogSourceStatus.ACTIVE, reason="Active"),
    )
    await session.commit()
    return auth_service, s_service, merchant, source


@pytest.mark.asyncio
async def test_cat_perm_001_fail_closed_default(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-001: Fail-closed default (no permissions = DENY)."""
    async with session_factory() as session:
        auth_service = CatalogAuthorizationService(session)
        # Random non-existent source
        res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=uuid4(),
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert res.decision == "DENY"
        assert res.reason_code == "DENY_SOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_cat_perm_002_deny_unverified_merchant(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-002: Deny if merchant is not VERIFIED."""
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)
        auth_service = CatalogAuthorizationService(session)

        merchant = await m_service.register_merchant(
            MerchantCreate(name="Unverified Brand", legal_name="Unverified Legal Ltd")
        )
        source = await s_service.register_source(
            SourceCreate(merchant_id=merchant.id, slug="unverified-src", name="Unverified Src")
        )
        await session.commit()

        res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert res.decision == "DENY"
        assert res.reason_code == "DENY_MERCHANT_NOT_VERIFIED"


@pytest.mark.asyncio
async def test_cat_perm_003_deny_inactive_source(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-003: Deny if source is not ACTIVE."""
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)
        auth_service = CatalogAuthorizationService(session)

        merchant = await m_service.register_merchant(
            MerchantCreate(name="Brand 3", legal_name="Brand 3 Legal Ltd")
        )
        await m_service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.VERIFIED,
                reason="Verified",
            ),
        )
        source = await s_service.register_source(
            SourceCreate(merchant_id=merchant.id, slug="pending-src", name="Pending Src")
        )
        await session.commit()

        res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert res.decision == "DENY"
        assert res.reason_code == "DENY_SOURCE_NOT_ACTIVE"


@pytest.mark.asyncio
async def test_cat_perm_004_deny_unverified_evidence(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-004: Deny if evidence is not VERIFIED."""
    async with session_factory() as session:
        (
            auth_service,
            s_service,
            merchant,
            source,
        ) = await _setup_verified_merchant_and_active_source(session, "src-ev-test")
        # Query existing evidence and mark it REJECTED
        ev_list = await auth_service.list_evidence(source.id)
        for e in ev_list:
            e.verification_status = EvidenceVerificationStatus.REJECTED.value
            await session.flush()
        await session.commit()

        res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert res.decision == "DENY"
        assert res.reason_code == "DENY_NO_VERIFIED_EVIDENCE"


@pytest.mark.asyncio
async def test_cat_perm_005_deny_missing_permission(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-005: Deny if requested permission is not granted."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-missing-perm"
        )
        res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.AFFILIATE_ATTRIBUTION.value,
            )
        )
        assert res.decision == "DENY"
        assert res.reason_code == "DENY_PERMISSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_cat_perm_006_allow_verified_and_granted(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-006: Allow when merchant VERIFIED, source ACTIVE, evidence VERIFIED, and permission GRANTED."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-allow-test"
        )
        res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert res.decision == "ALLOW"
        assert res.reason_code == "PERMITTED_BY_POLICY"
        assert res.permission_id is not None


@pytest.mark.asyncio
async def test_cat_perm_007_invariant_image_display_does_not_grant_ai_process(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-007: Invariant: IMAGE_DISPLAY does NOT grant IMAGE_AI_PROCESS."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-inv-ai"
        )
        # Grant IMAGE_DISPLAY
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.IMAGE_DISPLAY,
                granted_by="Brand Manager",
            )
        )
        await session.commit()

        # Check IMAGE_DISPLAY -> ALLOW
        display_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_DISPLAY.value,
            )
        )
        assert display_res.decision == "ALLOW"

        # Check IMAGE_AI_PROCESS -> MUST BE DENIED
        ai_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_AI_PROCESS.value,
            )
        )
        assert ai_res.decision == "DENY"
        assert ai_res.reason_code == "DENY_PERMISSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_cat_perm_008_invariant_image_store_does_not_grant_vto_process(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-008: Invariant: IMAGE_STORE does NOT grant VTO_PROCESS."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-inv-vto"
        )
        # Grant IMAGE_STORE
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.IMAGE_STORE,
                granted_by="Brand Ops",
            )
        )
        await session.commit()

        # Check IMAGE_STORE -> ALLOW
        store_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_STORE.value,
            )
        )
        assert store_res.decision == "ALLOW"

        # Check VTO_PROCESS -> MUST BE DENIED
        vto_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.VTO_PROCESS.value,
            )
        )
        assert vto_res.decision == "DENY"
        assert vto_res.reason_code == "DENY_PERMISSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_cat_perm_009_invariant_read_does_not_grant_display(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-009: Invariant: PRODUCT_DATA_READ does NOT grant PRODUCT_DISPLAY."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-inv-read"
        )
        # Only PRODUCT_DATA_READ is granted in setup
        read_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            )
        )
        assert read_res.decision == "ALLOW"

        display_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DISPLAY.value,
            )
        )
        assert display_res.decision == "DENY"
        assert display_res.reason_code == "DENY_PERMISSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_cat_perm_010_invariant_derivative_create_requires_explicit_permission(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-010: Invariant: DERIVATIVE_CREATE requires explicit permission."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-inv-deriv"
        )
        # Grant IMAGE_AI_PROCESS
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.IMAGE_AI_PROCESS,
                granted_by="Brand Legal",
            )
        )
        await session.commit()

        # DERIVATIVE_CREATE must be denied unless explicitly granted
        deriv_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.DERIVATIVE_CREATE.value,
            )
        )
        assert deriv_res.decision == "DENY"
        assert deriv_res.reason_code == "DENY_PERMISSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_cat_perm_011_timing_future_effective_at_denies(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-011: Permission effective_at in future -> DENY."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-future-eff"
        )
        future_eff = datetime.now(UTC) + timedelta(days=5)
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DISPLAY,
                granted_by="Legal",
                effective_at=future_eff,
            )
        )
        await session.commit()

        res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DISPLAY.value,
            )
        )
        assert res.decision == "DENY"
        assert res.reason_code == "DENY_PERMISSION_NOT_YET_EFFECTIVE"


@pytest.mark.asyncio
async def test_cat_perm_012_timing_past_expires_at_denies(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-012: Permission expires_at in past -> DENY."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-past-exp"
        )
        past_exp = datetime.now(UTC) - timedelta(days=2)
        past_eff = datetime.now(UTC) - timedelta(days=10)
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DISPLAY,
                granted_by="Legal",
                effective_at=past_eff,
                expires_at=past_exp,
            )
        )
        await session.commit()

        res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DISPLAY.value,
            )
        )
        assert res.decision == "DENY"
        assert res.reason_code == "DENY_PERMISSION_EXPIRED"


@pytest.mark.asyncio
async def test_cat_perm_013_revocation_denies(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-013: Permission revoked_at set -> DENY."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-revoked-perm"
        )
        perm = await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DISPLAY,
                granted_by="Legal",
            )
        )
        await session.commit()

        # Check ALLOW before revocation
        pre_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DISPLAY.value,
            )
        )
        assert pre_res.decision == "ALLOW"

        # Revoke permission
        await auth_service.revoke_permission(perm.id, reason="Legal terms terminated")
        await session.commit()

        post_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DISPLAY.value,
            )
        )
        assert post_res.decision == "DENY"
        assert post_res.reason_code == "DENY_PERMISSION_REVOKED"


@pytest.mark.asyncio
async def test_cat_perm_014_category_scope_restriction(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-014: Category restriction enforcement (allowed vs disallowed)."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-cat-scope"
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DISPLAY,
                granted_by="Legal",
                scope_categories=["apparel", "footwear"],
            )
        )
        await session.commit()

        # In-scope category
        in_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DISPLAY.value,
                category="apparel",
            )
        )
        assert in_res.decision == "ALLOW"

        # Out-of-scope category
        out_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DISPLAY.value,
                category="jewelry",
            )
        )
        assert out_res.decision == "DENY"
        assert out_res.reason_code == "DENY_CATEGORY_OUT_OF_SCOPE"


@pytest.mark.asyncio
async def test_cat_perm_015_market_scope_restriction(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-015: Market restriction enforcement (e.g. IN allowed, US disallowed)."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-market-scope"
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DISPLAY,
                granted_by="Legal",
                scope_markets=["IN", "AE"],
            )
        )
        await session.commit()

        # In-scope market
        in_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DISPLAY.value,
                market="IN",
            )
        )
        assert in_res.decision == "ALLOW"

        # Out-of-scope market
        out_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DISPLAY.value,
                market="US",
            )
        )
        assert out_res.decision == "DENY"
        assert out_res.reason_code == "DENY_MARKET_OUT_OF_SCOPE"


@pytest.mark.asyncio
async def test_cat_perm_016_processor_restrictions(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-016: Processor restriction enforcement."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-proc-scope"
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.IMAGE_AI_PROCESS,
                granted_by="Legal",
                processor_restrictions=["internal_segmenter_v1", "sam_vit_h"],
            )
        )
        await session.commit()

        # Allowed processor
        allow_proc = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_AI_PROCESS.value,
                processor_id="internal_segmenter_v1",
            )
        )
        assert allow_proc.decision == "ALLOW"

        # Disallowed external third-party processor
        deny_proc = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_AI_PROCESS.value,
                processor_id="third_party_cloud_api",
            )
        )
        assert deny_proc.decision == "DENY"
        assert deny_proc.reason_code == "DENY_PROCESSOR_NOT_PERMITTED"


@pytest.mark.asyncio
async def test_cat_perm_017_commercial_redirect_and_affiliate_attribution(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-017: Commercial redirect and affiliate attribution permissions."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-affiliate"
        )
        # Grant MERCHANT_REDIRECT
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.MERCHANT_REDIRECT,
                granted_by="Partnership Agreement",
            )
        )
        # Grant AFFILIATE_ATTRIBUTION
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.AFFILIATE_ATTRIBUTION,
                granted_by="Affiliate Agreement",
            )
        )
        await session.commit()

        redirect_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.MERCHANT_REDIRECT.value,
            )
        )
        assert redirect_res.decision == "ALLOW"

        affiliate_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.AFFILIATE_ATTRIBUTION.value,
            )
        )
        assert affiliate_res.decision == "ALLOW"


@pytest.mark.asyncio
async def test_cat_perm_018_structured_audit_logging(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-PERM-018: Structured audit log created for each evaluation decision."""
    async with session_factory() as session:
        auth_service, _, _, source = await _setup_verified_merchant_and_active_source(
            session, "src-audit-log"
        )
        context = AuthorizationContext(
            source_id=source.id,
            operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            product_id="SKU-TEST-999",
            category="apparel",
            market="IN",
            correlation_id="corr-audit-1234",
        )
        res = await auth_service.evaluate(context)
        await session.commit()

        assert res.decision == "ALLOW"

        # Verify entry in catalog_authorization_decisions
        stmt = select(CatalogAuthorizationDecision).where(
            CatalogAuthorizationDecision.source_id == source.id,
            CatalogAuthorizationDecision.correlation_id == "corr-audit-1234",
        )
        audit_res = await session.execute(stmt)
        record = audit_res.scalar_one_or_none()

        assert record is not None
        assert record.decision == "ALLOW"
        assert record.reason_code == "PERMITTED_BY_POLICY"
        assert record.operation == CatalogPermissionCode.PRODUCT_DATA_READ.value
        assert record.product_id == "SKU-TEST-999"
        assert record.category == "apparel"
        assert record.market == "IN"
