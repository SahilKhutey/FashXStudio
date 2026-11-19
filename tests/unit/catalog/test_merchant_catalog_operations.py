from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    IngestRun,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogPermissionStatus,
    CatalogSourcePermission,
    CatalogSourceStatus,
)
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from database.models.catalog_operations import (
    AuditAction,
    AuditActorRole,
    CatalogSourceSchedule,
    ErrorCategory,
    FailedStage,
    OperationalStatus,
    SyncMode,
)
from database.models.catalog_sync import CatalogIngestionQuarantine
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.image_permission_status_service import (
    ImagePermissionStatusService,
)
from fashx.catalog.operations.ingestion_report_service import (
    IngestionReportService,
)
from fashx.catalog.operations.manual_sync_service import ManualSyncService
from fashx.catalog.operations.merchant_product_removal_service import (
    MerchantProductRemovalService,
)
from fashx.catalog.operations.merchant_product_update_service import (
    MerchantProductUpdateService,
)
from fashx.catalog.operations.rejection_report_service import (
    RejectionReportService,
)
from fashx.catalog.operations.schemas import (
    ManualSyncRequest,
    MerchantOfferDeactivateRequest,
    MerchantProductOverrideRequest,
    SourceConnectionRequest,
    SourceOperationalStatusRequest,
    SourceScheduleRequest,
    SourceTakedownRequest,
)
from fashx.catalog.operations.source_audit_service import SourceAuditService
from fashx.catalog.operations.source_connection_service import (
    SourceConnectionService,
    mask_credential_reference,
)
from fashx.catalog.operations.source_lifecycle_service import SourceLifecycleService
from fashx.catalog.operations.source_takedown_service import SourceTakedownService
from fashx.catalog.operations.sync_schedule_service import SyncScheduleService
from fashx.catalog.operations.sync_status_service import SyncStatusService


async def create_test_merchant(session: AsyncSession, name: str = "Test Merchant") -> Merchant:
    merchant = Merchant(
        name=name,
        merchant_type="BRAND_DIRECT",
        country_code="IN",
        verification_status="VERIFIED",
    )
    session.add(merchant)
    await session.commit()
    await session.refresh(merchant)
    return merchant


async def create_test_source(
    session: AsyncSession,
    merchant_id: uuid.UUID,
    slug: str | None = None,
    is_enabled: bool = True,
    operational_status: str = "ENABLED",
    source_status: str = "AUTHORIZED",
) -> CatalogSource:
    source_slug = slug or f"src-{uuid.uuid4().hex[:8]}"
    source = CatalogSource(
        merchant_id=merchant_id,
        slug=source_slug,
        name=f"Source {source_slug}",
        kind="api",
        status="cleared",
        source_status=source_status,
        operational_status=operational_status,
        is_enabled=is_enabled,
        rights_display=True,
        rights_tryon=True,
        image_policy="mirror",
        refresh_hours=24,
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


# ============================================================================
# 5.6.1: Source Connection Management (OPS-001 to OPS-005)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_001_register_valid_source(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        service = SourceConnectionService(session)

        req = SourceConnectionRequest(
            merchant_id=merchant.id,
            slug="nordic-knitwear-api",
            name="Nordic Knitwear API",
            source_type="MERCHANT_API",
            adapter_name="generic_merchant_api",
            access_method="API_KEY",
            credential_secret_ref="secrets://fashx-prod/merchants/nordic/api-key",
            refresh_hours=12,
        )
        res = await service.connect_source(req)

        assert res.slug == "nordic-knitwear-api"
        assert res.source_status == CatalogSourceStatus.PENDING_REVIEW.value
        assert res.operational_status == OperationalStatus.ENABLED.value
        assert res.is_enabled is True
        assert res.masked_credential_ref == "secrets://fashx-prod/merchants/nordic/******"

        # Check default schedule was created
        sched = await session.scalar(
            select(CatalogSourceSchedule).where(CatalogSourceSchedule.source_id == res.id)
        )
        assert sched is not None
        assert sched.enabled is True
        assert sched.interval_minutes == 720  # 12 hours * 60


@pytest.mark.asyncio
async def test_ops_002_reject_duplicate_source_slug(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        await create_test_source(session, merchant.id, slug="duplicate-slug")

        service = SourceConnectionService(session)
        req = SourceConnectionRequest(
            merchant_id=merchant.id,
            slug="duplicate-slug",
            name="Duplicate Slug Source",
        )
        with pytest.raises(CatalogAuthorizationError) as exc_info:
            await service.connect_source(req)
        assert exc_info.value.code == "source_slug_conflict"


@pytest.mark.asyncio
async def test_ops_003_reject_nonexistent_merchant(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        service = SourceConnectionService(session)
        req = SourceConnectionRequest(
            merchant_id=uuid.uuid4(),
            slug="ghost-merchant-source",
            name="Ghost Source",
        )
        with pytest.raises(CatalogAuthorizationError) as exc_info:
            await service.connect_source(req)
        assert exc_info.value.code == "merchant_not_found"


@pytest.mark.asyncio
async def test_ops_004_credential_masking_utility() -> None:
    assert (
        mask_credential_reference("secrets://my-org/keys/live-key")
        == "secrets://my-org/keys/******"
    )
    assert (
        mask_credential_reference("arn:aws:secretsmanager:us-east-1:12345:secret:key")
        == "arn:aws:secretsmanager:us-east-1:12345:secret:******"
    )
    assert mask_credential_reference("plain-token-123456") == "******"
    assert mask_credential_reference(None) is None


# ============================================================================
# 5.6.2: Source Enable / Disable Lifecycle (OPS-006 to OPS-010)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_006_disable_source_and_pause_schedule(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id, is_enabled=True)

        # Create schedule
        schedule = CatalogSourceSchedule(
            source_id=source.id,
            merchant_id=merchant.id,
            enabled=True,
            interval_minutes=60,
        )
        session.add(schedule)
        await session.commit()

        service = SourceLifecycleService(session)
        req = SourceOperationalStatusRequest(
            target_status=OperationalStatus.DISABLED,
            reason="Merchant feed maintenance",
        )
        res = await service.update_operational_status(source.id, req, merchant_id=merchant.id)

        assert res.operational_status == "DISABLED"
        assert res.is_enabled is False

        # Verify DB state
        await session.refresh(source)
        await session.refresh(schedule)
        assert source.is_enabled is False
        assert source.operational_status == "DISABLED"
        assert schedule.enabled is False


@pytest.mark.asyncio
async def test_ops_007_disabling_source_aborts_running_jobs(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id, is_enabled=True)

        run1 = IngestRun(source_id=source.id, merchant_id=merchant.id, status="running")
        run2 = IngestRun(source_id=source.id, merchant_id=merchant.id, status="queued")
        run3 = IngestRun(source_id=source.id, merchant_id=merchant.id, status="ok")
        session.add_all([run1, run2, run3])
        await session.commit()

        service = SourceLifecycleService(session)
        req = SourceOperationalStatusRequest(
            target_status=OperationalStatus.DISABLED,
            reason="Emergency stop",
        )
        await service.update_operational_status(source.id, req, merchant_id=merchant.id)

        await session.refresh(run1)
        await session.refresh(run2)
        await session.refresh(run3)

        assert run1.status == "aborted"
        assert "Emergency stop" in (run1.error or "")
        assert run2.status == "aborted"
        assert run3.status == "ok"  # Completed job untouched


@pytest.mark.asyncio
async def test_ops_008_cannot_enable_revoked_or_suspended_source(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(
            session, merchant.id, source_status="REVOKED", is_enabled=False
        )

        service = SourceLifecycleService(session)
        req = SourceOperationalStatusRequest(
            target_status=OperationalStatus.ENABLED,
            reason="Attempting to re-enable revoked source",
        )
        with pytest.raises(CatalogAuthorizationError) as exc_info:
            await service.update_operational_status(source.id, req, merchant_id=merchant.id)
        assert exc_info.value.code == "source_authorization_blocked"


# ============================================================================
# 5.6.3: Manual Synchronization Trigger (OPS-011 to OPS-015)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_011_trigger_manual_sync_enqueues_run(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        service = ManualSyncService(session)
        req = ManualSyncRequest(sync_mode=SyncMode.FULL, idempotency_key="sync-req-001")
        res = await service.trigger_sync(source.id, req, merchant_id=merchant.id)

        assert res.status == "queued"
        assert res.sync_mode == "FULL"
        assert res.idempotency_key == "sync-req-001"
        assert res.is_duplicate_request is False


@pytest.mark.asyncio
async def test_ops_012_manual_sync_idempotency_returns_existing(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        service = ManualSyncService(session)
        req = ManualSyncRequest(
            sync_mode=SyncMode.INCREMENTAL, idempotency_key="idem-key-duplicate"
        )
        res1 = await service.trigger_sync(source.id, req, merchant_id=merchant.id)
        assert res1.is_duplicate_request is False

        # Re-send exact same idempotency key
        res2 = await service.trigger_sync(source.id, req, merchant_id=merchant.id)
        assert res2.is_duplicate_request is True
        assert res2.run_id == res1.run_id


@pytest.mark.asyncio
async def test_ops_013_manual_sync_fails_if_source_disabled(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(
            session, merchant.id, is_enabled=False, operational_status="DISABLED"
        )

        service = ManualSyncService(session)
        req = ManualSyncRequest(sync_mode=SyncMode.INCREMENTAL)
        with pytest.raises(CatalogAuthorizationError) as exc_info:
            await service.trigger_sync(source.id, req, merchant_id=merchant.id)
        assert exc_info.value.code == "source_disabled"


# ============================================================================
# 5.6.4: Scheduled Synchronization (OPS-016 to OPS-020)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_016_update_and_get_schedule(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        service = SyncScheduleService(session)
        req = SourceScheduleRequest(
            enabled=True,
            sync_mode=SyncMode.INCREMENTAL,
            interval_minutes=120,
            timezone="Asia/Kolkata",
        )
        res = await service.update_schedule(source.id, req, merchant_id=merchant.id)

        assert res.enabled is True
        assert res.interval_minutes == 120
        assert res.timezone == "Asia/Kolkata"
        assert res.next_run_at is not None

        # Fetch schedule
        fetched = await service.get_schedule(source.id, merchant_id=merchant.id)
        assert fetched.id == res.id
        assert fetched.interval_minutes == 120


@pytest.mark.asyncio
async def test_ops_017_reject_schedule_under_15_minutes(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        service = SyncScheduleService(session)
        # Using model_construct to bypass pydantic validation and test service validation
        req = SourceScheduleRequest.model_construct(
            enabled=True,
            sync_mode=SyncMode.INCREMENTAL,
            interval_minutes=10,
            cron_expression=None,
            timezone="UTC",
        )
        with pytest.raises(CatalogAuthorizationError) as exc_info:
            await service.update_schedule(source.id, req, merchant_id=merchant.id)
        assert exc_info.value.code == "invalid_interval"


@pytest.mark.asyncio
async def test_ops_019_due_schedule_detection(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id, is_enabled=True)

        past_time = datetime.now(UTC) - timedelta(minutes=5)
        schedule = CatalogSourceSchedule(
            source_id=source.id,
            merchant_id=merchant.id,
            enabled=True,
            interval_minutes=60,
            next_run_at=past_time,
        )
        session.add(schedule)
        await session.commit()

        service = SyncScheduleService(session)
        due = await service.get_due_schedules()

        assert len(due) == 1
        assert due[0].id == schedule.id
        # Schedule was advanced
        assert due[0].next_run_at > datetime.now(UTC)


# ============================================================================
# 5.6.5: Sync Status Dashboard (OPS-021 to OPS-023)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_021_sync_status_dashboard(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        now = datetime.now(UTC)
        run = IngestRun(
            source_id=source.id,
            merchant_id=merchant.id,
            sync_mode="INCREMENTAL",
            status="ok",
            started_at=now - timedelta(seconds=45),
            finished_at=now,
            counts={"fetched": 150, "inserted": 30, "updated": 120, "quarantined": 0},
        )
        session.add(run)
        await session.commit()

        service = SyncStatusService(session)
        status_res = await service.get_source_sync_status(source.id, merchant_id=merchant.id)

        assert status_res.source_id == source.id
        assert status_res.last_sync_status == "ok"
        assert status_res.duration_seconds is not None
        assert 44.0 <= status_res.duration_seconds <= 46.0
        assert status_res.counts["fetched"] == 150
        assert status_res.is_healthy is True


# ============================================================================
# 5.6.6: Ingestion Failure Reporting (OPS-024 to OPS-027)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_024_record_and_redact_sensitive_errors(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        run = IngestRun(source_id=source.id, merchant_id=merchant.id, status="failed")
        session.add(run)
        await session.commit()

        service = IngestionReportService(session)
        raw_msg = "HTTP 401 Unauthorized: Authorization Bearer sk_live_secret123456789 expired for token: tok_987654321"

        err = await service.record_error(
            ingest_run_id=run.id,
            source_id=source.id,
            merchant_id=merchant.id,
            error_code="AUTH_EXPIRED",
            error_category=ErrorCategory.AUTHENTICATION.value,
            failed_stage=FailedStage.FETCH.value,
            raw_error_message=raw_msg,
            retryable=True,
        )

        assert err.retryable is True
        assert "sk_live_secret123456789" not in err.safe_error_message
        assert "tok_987654321" not in err.safe_error_message
        assert "******" in err.safe_error_message

        # Query errors via service
        report = await service.get_errors(source_id=source.id, merchant_id=merchant.id)
        assert report.total_count == 1
        assert report.errors[0].error_code == "AUTH_EXPIRED"


# ============================================================================
# 5.6.7: Product Rejection Reporting (OPS-028 to OPS-030)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_028_quarantined_products_and_remediation_guidance(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        run = IngestRun(source_id=source.id, merchant_id=merchant.id, status="completed")
        session.add(run)
        await session.commit()

        q_item = CatalogIngestionQuarantine(
            ingest_run_id=run.id,
            source_id=source.id,
            source_product_id="SKU-9901",
            reason_code="MISSING_FIELD",
            field_name="brand",
            status="PENDING",
        )
        session.add(q_item)
        await session.commit()

        service = RejectionReportService(session)
        report = await service.get_rejection_report(source.id, merchant_id=merchant.id)

        assert report.total_count == 1
        rec = report.records[0]
        assert rec.source_product_id == "SKU-9901"
        assert rec.guidance.reason_code == "MISSING_FIELD"
        assert rec.guidance.severity == "BLOCKING"
        assert "mandatory product field is missing" in rec.guidance.summary


# ============================================================================
# 5.6.8: Image Permission Status Dashboard (OPS-031 to OPS-033)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_031_image_permission_matrix(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        # Grant only IMAGE_FETCH and IMAGE_DISPLAY, but not VTO_PROCESS
        now_dt = datetime.now(UTC)
        p1 = CatalogSourcePermission(
            source_id=source.id,
            permission_code=CatalogPermissionCode.IMAGE_FETCH.value,
            permission_status=CatalogPermissionStatus.GRANTED.value,
            granted_by="platform_admin",
            effective_at=now_dt,
        )
        p2 = CatalogSourcePermission(
            source_id=source.id,
            permission_code=CatalogPermissionCode.IMAGE_DISPLAY.value,
            permission_status=CatalogPermissionStatus.GRANTED.value,
            granted_by="platform_admin",
            effective_at=now_dt,
        )
        # Turn off tryon on source to test warnings
        source.rights_tryon = False
        session.add_all([p1, p2])

        # Add image assets
        img1 = CatalogImageAsset(
            source_id=source.id,
            merchant_id=merchant.id,
            source_product_id="P1",
            status=ImageAssetStatus.ACTIVE.value,
        )
        img2 = CatalogImageAsset(
            source_id=source.id,
            merchant_id=merchant.id,
            source_product_id="P2",
            status=ImageAssetStatus.SUSPENDED.value,
        )
        session.add_all([img1, img2])
        await session.commit()

        service = ImagePermissionStatusService(session)
        matrix = await service.get_image_permission_matrix(source.id, merchant_id=merchant.id)

        assert matrix.fetch_permitted is True
        assert matrix.display_permitted is True
        assert matrix.vto_permitted is False
        assert matrix.total_assets_count == 2
        assert matrix.active_assets_count == 1
        assert matrix.suspended_assets_count == 1
        assert any("VTO permission not granted" in w for w in matrix.warning_messages)


# ============================================================================
# 5.6.9: Source Takedown Workflow (OPS-034 to OPS-036)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_034_source_takedown_workflow(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id, is_enabled=True)

        garment = CanonicalGarment(
            display_name="Shirt", category="tops", active=True, in_stock=True
        )
        session.add(garment)
        await session.flush()

        offer = MerchantOffer(
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="SKU-OFFER-1",
            url="https://merchant.com/p1",
            price_minor=299900,
            status="ACTIVE",
            in_stock=True,
        )
        run = IngestRun(source_id=source.id, merchant_id=merchant.id, status="running")
        img = CatalogImageAsset(
            source_id=source.id,
            merchant_id=merchant.id,
            source_product_id="SKU-OFFER-1",
            status=ImageAssetStatus.ACTIVE.value,
        )
        session.add_all([offer, run, img])
        await session.commit()

        service = SourceTakedownService(session)
        req = SourceTakedownRequest(
            reason_code="LICENSE_TERMINATED",
            reason_text="Merchant contract terminated by mutual agreement",
            purge_images=True,
        )
        res = await service.execute_takedown(source.id, req)

        assert res.takedown_status == "COMPLETED"
        assert res.jobs_cancelled_count == 1
        assert res.offers_deactivated_count == 1
        assert res.images_purged_count == 1

        # Verify source suspension
        await session.refresh(source)
        await session.refresh(offer)
        await session.refresh(run)
        await session.refresh(img)

        assert source.source_status == "SUSPENDED"
        assert source.operational_status == "SUSPENDED"
        assert source.is_enabled is False
        assert offer.status == "SUSPENDED"
        assert offer.in_stock is False
        assert run.status == "aborted"
        assert img.status == ImageAssetStatus.SUSPENDED.value


# ============================================================================
# 5.6.10: Merchant Product Overrides (OPS-037 to OPS-038)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_037_apply_merchant_product_override(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        product = MerchantProduct(
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="P-100",
            title="Original Title",
            source_url="https://merchant.com/p100",
            price_minor=1000,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)

        service = MerchantProductUpdateService(session)
        req = MerchantProductOverrideRequest(
            field_name="title",
            override_value={"value": "Enhanced Premium Linen Shirt"},
            reason="Marketing copy enhancement",
        )
        res = await service.apply_product_override(product.id, req, merchant_id=merchant.id)

        assert res.field_name == "title"
        assert res.override_value == {"value": "Enhanced Premium Linen Shirt"}
        assert res.previous_value == {"value": "Original Title"}

        # Product updated immediately
        await session.refresh(product)
        assert product.title == "Enhanced Premium Linen Shirt"


@pytest.mark.asyncio
async def test_ops_038_reject_disallowed_source_managed_field_override(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        product = MerchantProduct(
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="P-200",
            title="T-Shirt",
            source_url="https://merchant.com/p200",
        )
        session.add(product)
        await session.commit()

        service = MerchantProductUpdateService(session)
        req = MerchantProductOverrideRequest(
            field_name="source_product_id",
            override_value={"value": "HACKED_SKU"},
        )
        with pytest.raises(CatalogAuthorizationError) as exc_info:
            await service.apply_product_override(product.id, req, merchant_id=merchant.id)
        assert exc_info.value.code == "field_override_disallowed"


# ============================================================================
# 5.6.11: Merchant Product Offer Removal & Canonical Garment Retention (OPS-039 to OPS-040)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_039_offer_deactivation_preserves_shared_canonical_garment(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant_a = await create_test_merchant(session, name="Merchant A")
        merchant_b = await create_test_merchant(session, name="Merchant B")
        source_a = await create_test_source(session, merchant_a.id)
        source_b = await create_test_source(session, merchant_b.id)

        # Shared canonical garment
        garment = CanonicalGarment(
            display_name="Shared Blue Oxford Shirt", category="tops", active=True, in_stock=True
        )
        session.add(garment)
        await session.flush()

        offer_a = MerchantOffer(
            garment_id=garment.id,
            merchant_id=merchant_a.id,
            source_id=source_a.id,
            source_product_id="SKU-A",
            url="https://merch-a.com/item",
            price_minor=199900,
            status="ACTIVE",
            in_stock=True,
        )
        offer_b = MerchantOffer(
            garment_id=garment.id,
            merchant_id=merchant_b.id,
            source_id=source_b.id,
            source_product_id="SKU-B",
            url="https://merch-b.com/item",
            price_minor=219900,
            status="ACTIVE",
            in_stock=True,
        )
        session.add_all([offer_a, offer_b])
        await session.commit()

        # Merchant A deactivates their offer
        service = MerchantProductRemovalService(session)
        req = MerchantOfferDeactivateRequest(reason="End of seasonal line")
        res = await service.deactivate_offer(offer_a.id, req, merchant_id=merchant_a.id)

        assert res.offer_status == "INACTIVE"
        assert (
            res.canonical_garment_active is True
        )  # Garment is PRESERVED because Merchant B still offers it!

        await session.refresh(garment)
        assert garment.active is True
        assert garment.in_stock is True


@pytest.mark.asyncio
async def test_ops_040_offer_deactivation_marks_garment_inactive_when_no_offers_left(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        garment = CanonicalGarment(
            display_name="Solo Garment", category="tops", active=True, in_stock=True
        )
        session.add(garment)
        await session.flush()

        sole_offer = MerchantOffer(
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="SKU-SOLO",
            url="https://merch.com/solo",
            price_minor=150000,
            status="ACTIVE",
            in_stock=True,
        )
        session.add(sole_offer)
        await session.commit()

        service = MerchantProductRemovalService(session)
        req = MerchantOfferDeactivateRequest(reason="Permanently discontinued")
        res = await service.deactivate_offer(sole_offer.id, req, merchant_id=merchant.id)

        assert res.offer_status == "INACTIVE"
        assert res.canonical_garment_active is False  # Inactive now since no other offers remain!

        await session.refresh(garment)
        assert garment.active is False
        assert garment.in_stock is False


# ============================================================================
# 5.6.12: Tenant Isolation and Audit Trail (OPS-041 to OPS-042)
# ============================================================================


@pytest.mark.asyncio
async def test_ops_041_tenant_isolation_prevents_cross_merchant_modification(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant_a = await create_test_merchant(session, name="Merchant A")
        merchant_b = await create_test_merchant(session, name="Merchant B")
        source_a = await create_test_source(session, merchant_a.id)

        # Merchant B attempts to disable Merchant A's source
        lifecycle_svc = SourceLifecycleService(session)
        req = SourceOperationalStatusRequest(
            target_status=OperationalStatus.DISABLED, reason="Malicious attempt"
        )

        with pytest.raises(CatalogAuthorizationError) as exc_info:
            await lifecycle_svc.update_operational_status(
                source_a.id, req, merchant_id=merchant_b.id
            )
        assert exc_info.value.code == "tenant_isolation_violation"


@pytest.mark.asyncio
async def test_ops_042_immutable_audit_logging_and_querying(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        audit_svc = SourceAuditService(session)
        await audit_svc.log_event(
            actor_id=uuid.uuid4(),
            actor_role=AuditActorRole.MERCHANT_OPERATOR.value,
            merchant_id=merchant.id,
            source_id=source.id,
            entity_type="SOURCE",
            action=AuditAction.SOURCE_STATUS_CHANGED.value,
            safe_change_summary={"change": "Enabled source"},
        )

        events, total = await audit_svc.get_audit_events(merchant_id=merchant.id)
        assert total == 1
        assert events[0].action == AuditAction.SOURCE_STATUS_CHANGED.value
        assert events[0].merchant_id == merchant.id
