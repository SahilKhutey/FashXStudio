from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog_auth import (
    CatalogAccessMethod,
    CatalogPermissionCode,
    CatalogSourceStatus,
    CatalogSourceType,
    EvidenceVerificationStatus,
    MerchantVerificationStatus,
)
from fashx.catalog.authorization.schemas import EvidenceCreate, PermissionCreate
from fashx.catalog.authorization.service import CatalogAuthorizationService
from fashx.catalog.errors import (
    MerchantVerificationError,
    SourceLifecycleError,
)
from fashx.catalog.merchants.schemas import (
    MerchantCreate,
    MerchantVerificationRequest,
)
from fashx.catalog.merchants.service import MerchantService
from fashx.catalog.sources.schemas import (
    SourceCreate,
    SourceStatusUpdate,
)
from fashx.catalog.sources.service import CatalogSourceService


@pytest.mark.asyncio
async def test_cat_auth_001_merchant_registration(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-001: Merchant registration with legal identity, country, and contacts."""
    async with session_factory() as session:
        service = MerchantService(session)
        payload = MerchantCreate(
            name="Zara India",
            merchant_type="brand",
            legal_name="Inditex Trent Retail India Private Limited",
            display_name="Zara",
            website="https://www.zara.com/in",
            country_code="IN",
            registration_reference="U74900MH2009FTC194883",
            primary_contact_id=uuid4(),
            technical_contact_id=uuid4(),
            takedown_contact_id=uuid4(),
        )
        merchant = await service.register_merchant(payload)
        await session.commit()

        assert merchant.id is not None
        assert merchant.name == "Zara India"
        assert merchant.legal_name == "Inditex Trent Retail India Private Limited"
        assert merchant.country_code == "IN"
        assert merchant.verification_status == MerchantVerificationStatus.UNVERIFIED.value
        assert merchant.primary_contact_id == payload.primary_contact_id


@pytest.mark.asyncio
async def test_cat_auth_002_duplicate_legal_name_and_registration(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-002: Duplicate legal name / registration validation rejected."""
    async with session_factory() as session:
        service = MerchantService(session)
        p1 = MerchantCreate(
            name="H&M India",
            merchant_type="retailer",
            legal_name="H & M Hennes & Mauritz Retail Private Limited",
            registration_reference="U51909DL2013FTC261908",
        )
        await service.register_merchant(p1)
        await session.commit()

        # Duplicate legal name
        p2 = MerchantCreate(
            name="H&M India Alternate",
            merchant_type="retailer",
            legal_name="H & M Hennes & Mauritz Retail Private Limited",
        )
        with pytest.raises(MerchantVerificationError) as exc:
            await service.register_merchant(p2)
        assert exc.value.code == "merchant_legal_name_conflict"

        # Duplicate registration reference
        p3 = MerchantCreate(
            name="H&M Distinct",
            merchant_type="retailer",
            legal_name="Different Legal Name Private Limited",
            registration_reference="U51909DL2013FTC261908",
        )
        with pytest.raises(MerchantVerificationError) as exc_reg:
            await service.register_merchant(p3)
        assert exc_reg.value.code == "merchant_registration_conflict"


@pytest.mark.asyncio
async def test_cat_auth_003_merchant_verification_workflow(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-003: Merchant verification workflow (UNVERIFIED -> UNDER_REVIEW -> VERIFIED)."""
    async with session_factory() as session:
        service = MerchantService(session)
        merchant = await service.register_merchant(
            MerchantCreate(
                name="FabIndia",
                legal_name="Fabindia Limited",
                country_code="IN",
            )
        )
        await session.commit()

        # Transition UNVERIFIED -> UNDER_REVIEW
        m_review = await service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.UNDER_REVIEW,
                reason="Verification documents submitted for review.",
            ),
        )
        assert m_review.verification_status == MerchantVerificationStatus.UNDER_REVIEW.value

        # Transition UNDER_REVIEW -> VERIFIED
        m_verified = await service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.VERIFIED,
                reason="MCA corporate registry confirmed and countersigned agreement validated.",
                reviewer_id=uuid4(),
            ),
        )
        assert m_verified.verification_status == MerchantVerificationStatus.VERIFIED.value


@pytest.mark.asyncio
async def test_cat_auth_004_merchant_rejection_and_suspension(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-004: Merchant rejection and suspension workflow."""
    async with session_factory() as session:
        service = MerchantService(session)
        merchant = await service.register_merchant(
            MerchantCreate(
                name="Suspicious Seller",
                legal_name="Unknown Entity Ltd",
            )
        )
        await session.commit()

        # Direct rejection from UNVERIFIED
        m_rejected = await service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.REJECTED,
                reason="Inauthentic registration documents provided.",
            ),
        )
        assert m_rejected.verification_status == MerchantVerificationStatus.REJECTED.value

        # Invalid transition: REJECTED directly to VERIFIED is forbidden
        with pytest.raises(MerchantVerificationError) as exc:
            await service.verify_merchant(
                merchant.id,
                MerchantVerificationRequest(
                    verification_status=MerchantVerificationStatus.VERIFIED,
                    reason="Bypassing re-review",
                ),
            )
        assert exc.value.code == "invalid_merchant_transition"


@pytest.mark.asyncio
async def test_cat_auth_005_source_registration_under_merchant(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-005: Source registration under merchant."""
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)

        merchant = await m_service.register_merchant(
            MerchantCreate(
                name="Uniqlo India",
                legal_name="Uniqlo India Private Limited",
            )
        )
        await session.commit()

        source_payload = SourceCreate(
            merchant_id=merchant.id,
            slug="uniqlo-api-prod",
            name="Uniqlo Production Catalog API",
            source_type=CatalogSourceType.MERCHANT_API,
            access_method=CatalogAccessMethod.OAUTH2,
            credential_secret_ref="secrets/catalog/uniqlo/oauth",
            market_codes=["IN"],
            category_codes=["apparel", "accessories"],
        )
        source = await s_service.register_source(source_payload)
        await session.commit()

        assert source.id is not None
        assert source.slug == "uniqlo-api-prod"
        assert source.source_status == CatalogSourceStatus.PENDING_REVIEW.value
        assert source.merchant_id == merchant.id


@pytest.mark.asyncio
async def test_cat_auth_006_multiple_sources_per_merchant(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-006: Multiple sources per merchant (API + Feed)."""
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)

        merchant = await m_service.register_merchant(
            MerchantCreate(
                name="Nike India",
                legal_name="Nike India Private Limited",
            )
        )
        await session.commit()

        s1 = await s_service.register_source(
            SourceCreate(
                merchant_id=merchant.id,
                slug="nike-direct-api",
                name="Nike Direct API",
                source_type=CatalogSourceType.MERCHANT_API,
                access_method=CatalogAccessMethod.API_KEY,
            )
        )
        s2 = await s_service.register_source(
            SourceCreate(
                merchant_id=merchant.id,
                slug="nike-partner-feed",
                name="Nike Nightly Partner Feed",
                source_type=CatalogSourceType.MERCHANT_FEED,
                access_method=CatalogAccessMethod.HTTPS_FEED,
            )
        )
        await session.commit()

        sources = await s_service.list_sources(merchant_id=merchant.id)
        assert len(sources) == 2
        slugs = {s.slug for s in sources}
        assert "nike-direct-api" in slugs
        assert "nike-partner-feed" in slugs


@pytest.mark.asyncio
async def test_cat_auth_007_source_lifecycle_transitions(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-007: Source lifecycle transitions (PENDING_REVIEW -> APPROVED -> ACTIVE)."""
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)
        auth_service = CatalogAuthorizationService(session)

        # 1. Register & Verify Merchant
        merchant = await m_service.register_merchant(
            MerchantCreate(
                name="Levi Strauss India",
                legal_name="Levi Strauss (India) Private Limited",
            )
        )
        await m_service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.VERIFIED,
                reason="Verified corporate registration",
            ),
        )
        await session.commit()

        # 2. Register Source
        source = await s_service.register_source(
            SourceCreate(
                merchant_id=merchant.id,
                slug="levis-api",
                name="Levi's API",
            )
        )
        await session.commit()

        # 3. Transition to APPROVED
        s_approved = await s_service.update_source_status(
            source.id,
            SourceStatusUpdate(
                target_status=CatalogSourceStatus.APPROVED,
                reason="Technical handshake verified",
            ),
        )
        assert s_approved.source_status == CatalogSourceStatus.APPROVED.value

        # 4. Attach verified evidence and granted permission
        evidence = await auth_service.add_evidence(
            EvidenceCreate(
                source_id=source.id,
                evidence_type="CONTRACT",
                document_reference="contracts/2026/levis-msa-v1.pdf",
                document_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                verification_status=EvidenceVerificationStatus.VERIFIED,
            )
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DATA_READ,
                granted_by="Levi's Legal Counsel",
                evidence_id=evidence.id,
            )
        )
        await session.commit()

        # 5. Transition to ACTIVE
        s_active = await s_service.update_source_status(
            source.id,
            SourceStatusUpdate(
                target_status=CatalogSourceStatus.ACTIVE,
                reason="Evidence and permissions verified.",
            ),
        )
        assert s_active.source_status == CatalogSourceStatus.ACTIVE.value
        assert s_active.status == "cleared"
        assert s_active.rights_display is True


@pytest.mark.asyncio
async def test_cat_auth_008_source_activation_blocked_without_evidence_or_permissions(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-008: Source activation blocked without verified evidence or permissions."""
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)

        # 1. Merchant verified
        merchant = await m_service.register_merchant(
            MerchantCreate(
                name="Puma India",
                legal_name="Puma Sports India Private Limited",
            )
        )
        await m_service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.VERIFIED,
                reason="Verified",
            ),
        )

        # 2. Source registered and approved
        source = await s_service.register_source(
            SourceCreate(
                merchant_id=merchant.id,
                slug="puma-api",
                name="Puma API",
            )
        )
        await s_service.update_source_status(
            source.id,
            SourceStatusUpdate(
                target_status=CatalogSourceStatus.APPROVED,
                reason="Technical connection established",
            ),
        )
        await session.commit()

        # 3. Attempt ACTIVE without evidence -> blocked
        with pytest.raises(SourceLifecycleError) as exc_ev:
            await s_service.update_source_status(
                source.id,
                SourceStatusUpdate(
                    target_status=CatalogSourceStatus.ACTIVE,
                    reason="Try activating without evidence",
                ),
            )
        assert exc_ev.value.code == "no_verified_evidence"


@pytest.mark.asyncio
async def test_cat_auth_009_source_suspension_denies_rights(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-009: Source suspension propagates to inactive state and revokes rights."""
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)
        auth_service = CatalogAuthorizationService(session)

        merchant = await m_service.register_merchant(
            MerchantCreate(
                name="Adidas India",
                legal_name="Adidas India Marketing Private Limited",
            )
        )
        await m_service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.VERIFIED,
                reason="Verified",
            ),
        )

        source = await s_service.register_source(
            SourceCreate(
                merchant_id=merchant.id,
                slug="adidas-feed",
                name="Adidas Feed",
            )
        )
        await s_service.update_source_status(
            source.id,
            SourceStatusUpdate(
                target_status=CatalogSourceStatus.APPROVED,
                reason="Approved",
            ),
        )
        ev = await auth_service.add_evidence(
            EvidenceCreate(
                source_id=source.id,
                document_reference="contracts/adidas.pdf",
                verification_status=EvidenceVerificationStatus.VERIFIED,
            )
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DATA_READ,
                granted_by="Adidas Legal",
                evidence_id=ev.id,
            )
        )
        await s_service.update_source_status(
            source.id,
            SourceStatusUpdate(
                target_status=CatalogSourceStatus.ACTIVE,
                reason="Active",
            ),
        )
        await session.commit()

        # Suspend source
        s_suspended = await s_service.suspend_source(
            source.id, reason="Compliance audit in progress"
        )
        await session.commit()

        assert s_suspended.source_status == CatalogSourceStatus.SUSPENDED.value
        assert s_suspended.status == "suspended"
        assert s_suspended.rights_display is False
        assert s_suspended.rights_tryon is False


@pytest.mark.asyncio
async def test_cat_auth_010_source_expiry_enforcement(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT-AUTH-010: Source expiry date enforcement via CatalogExpiryWorker."""
    from fashx.catalog.authorization.expiry_worker import CatalogExpiryWorker

    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)
        auth_service = CatalogAuthorizationService(session)

        merchant = await m_service.register_merchant(
            MerchantCreate(
                name="Marks & Spencer India",
                legal_name="Marks and Spencer Reliance India Private Limited",
            )
        )
        await m_service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.VERIFIED,
                reason="Verified",
            ),
        )

        now = datetime.now(UTC)
        past_expiry = now - timedelta(days=1)
        source = await s_service.register_source(
            SourceCreate(
                merchant_id=merchant.id,
                slug="mns-promo-source",
                name="M&S Promo Source",
                expires_at=past_expiry,
            )
        )
        await s_service.update_source_status(
            source.id,
            SourceStatusUpdate(target_status=CatalogSourceStatus.APPROVED, reason="Approved"),
        )
        ev = await auth_service.add_evidence(
            EvidenceCreate(
                source_id=source.id,
                document_reference="contracts/mns.pdf",
                verification_status=EvidenceVerificationStatus.VERIFIED,
            )
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DATA_READ,
                granted_by="M&S Counsel",
                evidence_id=ev.id,
            )
        )
        await s_service.update_source_status(
            source.id,
            SourceStatusUpdate(target_status=CatalogSourceStatus.ACTIVE, reason="Active"),
        )
        await session.commit()

        # Run expiry scan
        result = await CatalogExpiryWorker.scan_and_expire(session, now=now)
        await session.commit()

        assert result.expired_sources >= 1
        refreshed_source = await s_service.get_source(source.id)
        assert refreshed_source.source_status == CatalogSourceStatus.EXPIRED.value
        assert refreshed_source.status == "suspended"
