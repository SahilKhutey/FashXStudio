from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import MerchantProduct
from database.models.catalog_auth import (
    CatalogAuthorizationDecision,
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
from fashx.catalog.errors import SourceLifecycleError
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
from fashx.catalog.takedowns.schemas import (
    TakedownRequestCreate,
    TakedownResolutionRequest,
)
from fashx.catalog.takedowns.service import CatalogTakedownService
from fashx.catalog.takedowns.worker import TakedownAsyncWorker


@pytest.mark.asyncio
async def test_full_catalog_authorization_e2e_journey(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """End-to-end 19+ step integration scenario verifying merchant onboarding,

    source registration, evidence attachment, granular permissions, strict
    AI non-inference, takedown lifecycle, and complete audit logging.
    """
    async with session_factory() as session:
        m_service = MerchantService(session)
        s_service = CatalogSourceService(session)
        auth_service = CatalogAuthorizationService(session)
        take_service = CatalogTakedownService(session)

        corr_id = f"corr-e2e-{uuid4()}"

        # 1. Merchant submits registration
        merchant = await m_service.register_merchant(
            MerchantCreate(
                name="Raymond India",
                merchant_type="brand",
                legal_name="Raymond Limited",
                display_name="Raymond",
                website="https://www.raymond.in",
                country_code="IN",
                registration_reference="L17117MH1925PLC001208",
            )
        )
        assert merchant.verification_status == MerchantVerificationStatus.UNVERIFIED.value

        # 2. Source registered under UNVERIFIED merchant
        source = await s_service.register_source(
            SourceCreate(
                merchant_id=merchant.id,
                slug="raymond-official-api",
                name="Raymond Official API",
            )
        )
        assert source.source_status == CatalogSourceStatus.PENDING_REVIEW.value

        # 3. Attempting to approve source fails because merchant is UNVERIFIED
        with pytest.raises(SourceLifecycleError) as exc_app:
            await s_service.update_source_status(
                source.id,
                SourceStatusUpdate(
                    target_status=CatalogSourceStatus.APPROVED,
                    reason="Try approving while unverified",
                ),
            )
        assert exc_app.value.code == "merchant_not_verified"

        # 4. Reviewer reviews identity & approves verification
        reviewer_id = uuid4()
        m_verified = await m_service.verify_merchant(
            merchant.id,
            MerchantVerificationRequest(
                verification_status=MerchantVerificationStatus.VERIFIED,
                reason="MCA verification passed, GSTIN active",
                reviewer_id=reviewer_id,
            ),
        )
        assert m_verified.verification_status == MerchantVerificationStatus.VERIFIED.value

        # 5. Now source can transition to APPROVED
        s_app = await s_service.update_source_status(
            source.id,
            SourceStatusUpdate(
                target_status=CatalogSourceStatus.APPROVED,
                reason="Merchant verified, endpoint connectivity validated",
            ),
        )
        assert s_app.source_status == CatalogSourceStatus.APPROVED.value

        # 6. Activation fails without evidence and permissions
        with pytest.raises(SourceLifecycleError) as exc_act:
            await s_service.update_source_status(
                source.id,
                SourceStatusUpdate(
                    target_status=CatalogSourceStatus.ACTIVE,
                    reason="Premature activation attempt",
                ),
            )
        assert exc_act.value.code == "no_verified_evidence"

        # 7. Authorization evaluator at this stage denies
        res_pre = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
                correlation_id=corr_id,
            )
        )
        assert res_pre.decision == "DENY"
        assert res_pre.reason_code == "DENY_SOURCE_NOT_ACTIVE"

        # 8. Upload contractual authorization evidence
        evidence = await auth_service.add_evidence(
            EvidenceCreate(
                source_id=source.id,
                evidence_type="CONTRACT",
                document_reference="s3://fashx-contracts/2026/raymond-msa-v1.pdf",
                document_sha256="b4c9354226cf7165bb0d32bb39832cb19e27c00e1ccfc2e42d7658be0a0da387",
                agreement_reference="FASHX-RAYMOND-2026-001",
                agreement_version="1.0",
                granted_by_name="Legal Director Raymond",
                granted_by_role="General Counsel",
                verified_by=reviewer_id,
                verification_status=EvidenceVerificationStatus.VERIFIED,
            )
        )
        assert evidence.verification_status == EvidenceVerificationStatus.VERIFIED.value

        # 9. Grant PRODUCT_DATA_READ & PRODUCT_DATA_STORE
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DATA_READ,
                granted_by="General Counsel",
                evidence_id=evidence.id,
            )
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.PRODUCT_DATA_STORE,
                granted_by="General Counsel",
                evidence_id=evidence.id,
            )
        )

        # 10. Grant IMAGE_FETCH and IMAGE_DISPLAY scoped to category "apparel" and market "IN"
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.IMAGE_FETCH,
                granted_by="General Counsel",
                evidence_id=evidence.id,
                scope_categories=["apparel"],
                scope_markets=["IN"],
            )
        )
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.IMAGE_DISPLAY,
                granted_by="General Counsel",
                evidence_id=evidence.id,
                scope_categories=["apparel"],
                scope_markets=["IN"],
            )
        )

        # 11. Now activate source
        s_act = await s_service.update_source_status(
            source.id,
            SourceStatusUpdate(
                target_status=CatalogSourceStatus.ACTIVE,
                reason="Evidence verified and baseline permissions granted",
            ),
        )
        assert s_act.source_status == CatalogSourceStatus.ACTIVE.value
        assert s_act.rights_display is True

        # 12. Evaluator allows PRODUCT_DATA_READ
        eval_read = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
                correlation_id=corr_id,
            )
        )
        assert eval_read.decision == "ALLOW"

        # 13. Evaluator allows IMAGE_DISPLAY for in-scope category & market
        eval_disp_ok = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_DISPLAY.value,
                category="apparel",
                market="IN",
                correlation_id=corr_id,
            )
        )
        assert eval_disp_ok.decision == "ALLOW"

        # 14. Evaluator strictly DENIES IMAGE_AI_PROCESS (Not granted, non-inference)
        eval_ai_deny = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_AI_PROCESS.value,
                category="apparel",
                market="IN",
                correlation_id=corr_id,
            )
        )
        assert eval_ai_deny.decision == "DENY"
        assert eval_ai_deny.reason_code == "DENY_PERMISSION_NOT_FOUND"

        # 15. Evaluator strictly DENIES VTO_PROCESS (Not granted, non-inference)
        eval_vto_deny = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.VTO_PROCESS.value,
                category="apparel",
                market="IN",
                correlation_id=corr_id,
            )
        )
        assert eval_vto_deny.decision == "DENY"
        assert eval_vto_deny.reason_code == "DENY_PERMISSION_NOT_FOUND"

        # 16. Evaluator strictly DENIES IMAGE_DISPLAY for out-of-scope market
        eval_mkt_deny = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_DISPLAY.value,
                category="apparel",
                market="US",
                correlation_id=corr_id,
            )
        )
        assert eval_mkt_deny.decision == "DENY"
        assert eval_mkt_deny.reason_code == "DENY_MARKET_OUT_OF_SCOPE"

        # 17. Grant explicit IMAGE_AI_PROCESS with processor restriction
        await auth_service.grant_permission(
            PermissionCreate(
                source_id=source.id,
                permission_code=CatalogPermissionCode.IMAGE_AI_PROCESS,
                granted_by="General Counsel Addendum",
                evidence_id=evidence.id,
                processor_restrictions=["internal_segmenter_v1"],
            )
        )

        # Allowed processor passes
        eval_ai_ok = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_AI_PROCESS.value,
                processor_id="internal_segmenter_v1",
                correlation_id=corr_id,
            )
        )
        assert eval_ai_ok.decision == "ALLOW"

        # Disallowed external processor fails
        eval_ai_ext_deny = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.IMAGE_AI_PROCESS.value,
                processor_id="unapproved_external_vendor",
                correlation_id=corr_id,
            )
        )
        assert eval_ai_ext_deny.decision == "DENY"
        assert eval_ai_ext_deny.reason_code == "DENY_PROCESSOR_NOT_PERMITTED"

        # 18. Takedown incident occurs
        # Seed merchant product
        p = MerchantProduct(
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="RAYMOND-SUIT-001",
            title="Raymond Classic Wool Suit",
            source_url="https://www.raymond.in/suit-001",
            status="active",
        )
        session.add(p)
        await session.flush()

        td = await take_service.initiate_takedown(
            TakedownRequestCreate(
                source_id=source.id,
                reason_code=TakedownReasonCode.IMAGE_RIGHTS_DISPUTE,
                requested_by="Brand Protection Agency",
                request_reference="DMCA-2026-RAY-01",
            )
        )
        assert td.status == TakedownStatus.SUSPENDED.value

        # Source is immediately suspended
        ref_s = await s_service.get_source(source.id)
        assert ref_s.source_status == CatalogSourceStatus.SUSPENDED.value
        assert ref_s.rights_display is False

        # All operations fail
        eval_td_deny = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
                correlation_id=corr_id,
            )
        )
        assert eval_td_deny.decision == "DENY"

        # Worker unpublishes products
        unpub_count = await TakedownAsyncWorker.process_unpublishing(
            session=session, takedown_id=td.id, source_id=source.id
        )
        assert unpub_count == 1
        assert p.status == "suspended"

        # 19. Takedown resolution and administrative resumption
        await take_service.resolve_takedown(
            td.id,
            TakedownResolutionRequest(
                resolution_notes="Disputed imagery removed; replacement brand catalog provided.",
                reviewer_id=reviewer_id,
            ),
        )
        resumed_s = await s_service.resume_source(
            source.id, reason="Compliance confirmed, replacement verified"
        )
        assert resumed_s.source_status == CatalogSourceStatus.ACTIVE.value
        assert resumed_s.rights_display is True

        # Operations resume
        eval_post_res = await auth_service.evaluate(
            AuthorizationContext(
                source_id=source.id,
                operation=CatalogPermissionCode.PRODUCT_DATA_READ.value,
                correlation_id=corr_id,
            )
        )
        assert eval_post_res.decision == "ALLOW"

        # Verify audit records exist for this correlation_id
        stmt = select(CatalogAuthorizationDecision).where(
            CatalogAuthorizationDecision.correlation_id == corr_id
        )
        decisions_res = await session.execute(stmt)
        decisions = decisions_res.scalars().all()
        assert len(decisions) >= 7
        dec_types = {d.decision for d in decisions}
        assert "ALLOW" in dec_types
        assert "DENY" in dec_types
