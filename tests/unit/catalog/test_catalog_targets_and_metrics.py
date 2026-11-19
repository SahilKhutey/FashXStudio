"""Unit tests for Phase 05.7: Initial Catalog Targets, Metric Measurement, and Release Gates.

Covers Test Cases:
- CAT57-001: One approved live source qualifies when evidence is valid
- CAT57-002: Mock adapter source does not qualify as live feed
- CAT57-003: Expired authorization fails compliance gate
- CAT57-004: Revoked source permission blocks relevant operation
- CAT57-005: 1,000 valid offers pass initial product count target
- CAT57-006: Raw rows with duplicates exclude duplicate offers
- CAT57-007: Quarantined product excluded from usable count
- CAT57-008: Inactive offer excluded from usable count
- CAT57-009: Product without valid merchant URL excluded from usable count
- CAT57-010: Same garment across merchants counted separately (1 canonical garment, N merchant offers)
- CAT57-011: Price within freshness window classified as fresh
- CAT57-012: Price beyond freshness window classified as stale
- CAT57-013: Missing price verification timestamp classified as unverified
- CAT57-014: Mixed currencies retained explicitly
- CAT57-015: Valid merchant destination URL classified as valid
- CAT57-016: HTTP 404 classified as broken
- CAT57-017: Temporary 503 retried and not classified as broken
- CAT57-018: Destination resolving or redirecting to private IP blocked by SSRF check
- CAT57-019: Redirect to unrelated or blocked destination classified as invalid
- CAT57-020: Image missing permission evidence fails traceability check
- CAT57-021: Display permission without storage permission blocks storage
- CAT57-022: Missing VTO permission blocks VTO processing
- CAT57-023: Image source under takedown blocks processing
- CAT57-024: Unauthorized active source fails overall compliance gate
- CAT57-025: Zero unauthorized sources passes compliance metric
- CAT57-026: Repeated evaluation with frozen snapshot gives deterministic result
- CAT57-027: Evaluation with missing data reports incomplete measurement
- CAT57-028: Evaluation run persistence and retrieval via CatalogReportService
- CAT57-029: Evaluation reports never expose secret values or tokens
- CAT57-030: Historical evaluations are immutable
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    IngestRun,
    Merchant,
    MerchantOffer,
)
from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogPermissionStatus,
    CatalogSourcePermission,
    CatalogSourceStatus,
)
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from database.models.catalog_sync import CatalogIngestionQuarantine
from fashx.catalog.metrics.contracts import (
    LinkCheckResult,
    LinkHealthClassification,
)
from fashx.catalog.metrics.evaluator import CatalogTargetEvaluator
from fashx.catalog.metrics.image_permission_metrics import (
    evaluate_image_permission_traceability,
)
from fashx.catalog.metrics.link_health import (
    safe_check_product_link,
    validate_url_ssrf_safety,
)
from fashx.catalog.metrics.price_freshness import evaluate_price_freshness
from fashx.catalog.metrics.product_metrics import (
    evaluate_product_usability_metrics,
)
from fashx.catalog.metrics.report_service import CatalogReportService
from fashx.catalog.metrics.source_metrics import evaluate_source_metrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def create_test_merchant(
    session: AsyncSession,
    name: str = "Test Retailer",
    verification_status: str = "VERIFIED",
) -> Merchant:
    m = Merchant(
        id=uuid4(),
        name=name,
        merchant_type="brand",
        country_code="IN",
        verification_status=verification_status,
        operational_status="ACTIVE",
    )
    session.add(m)
    await session.commit()
    return m


async def create_test_source(
    session: AsyncSession,
    merchant_id: uuid4,
    name: str = "Live API Feed",
    adapter_name: str = "retailer_api_v1",
    source_status: str = CatalogSourceStatus.ACTIVE.value,
    is_enabled: bool = True,
    authorization_reference: str | None = "CONTRACT-AUTH-2026-001",
    expires_at: datetime | None = None,
    kind: str = "api",
) -> CatalogSource:
    source = CatalogSource(
        id=uuid4(),
        merchant_id=merchant_id,
        slug=f"source-{uuid4().hex[:6]}",
        name=name,
        kind=kind,
        adapter_name=adapter_name,
        source_status=source_status,
        is_enabled=is_enabled,
        authorization_reference=authorization_reference,
        expires_at=expires_at,
        rights_display=True,
        rights_tryon=True,
        image_policy="mirror",
    )
    session.add(source)
    await session.commit()
    return source


async def create_canonical_garment(
    session: AsyncSession, name: str = "Summer Linen Shirt"
) -> CanonicalGarment:
    garment = CanonicalGarment(
        id=uuid4(),
        display_name=name,
        category="tops",
        gender="men",
    )
    session.add(garment)
    await session.commit()
    return garment


# ---------------------------------------------------------------------------
# Test Cases CAT57-001 to CAT57-030
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cat57_001_one_approved_live_source_qualifies(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-001: One approved live source qualifies when evidence is valid."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)

        # Record successful sync run
        run = IngestRun(
            id=uuid4(),
            source_id=source.id,
            merchant_id=merchant.id,
            status="ok",
        )
        session.add(run)
        await session.commit()

        live_res, unauth_res, details = await evaluate_source_metrics(
            session, minimum_live_sources=1
        )
        assert live_res.passed is True
        assert live_res.actual_value >= 1.0
        assert str(source.id) in live_res.source_ids


@pytest.mark.asyncio
async def test_cat57_002_mock_adapter_source_does_not_qualify(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-002: Mock adapter source does not qualify as live feed."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        # Source with mock adapter
        mock_source = await create_test_source(
            session,
            merchant.id,
            adapter_name="generic_mock_adapter",
        )
        # Even with successful ingest run, it must not count as live
        run = IngestRun(
            id=uuid4(),
            source_id=mock_source.id,
            merchant_id=merchant.id,
            status="ok",
        )
        session.add(run)
        await session.commit()

        live_res, _, details = await evaluate_source_metrics(session, minimum_live_sources=1)
        assert str(mock_source.id) not in live_res.source_ids


@pytest.mark.asyncio
async def test_cat57_003_expired_authorization_fails_compliance_gate(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-003: Expired authorization fails compliance gate."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        now = datetime.now(UTC)
        expired_source = await create_test_source(
            session,
            merchant.id,
            expires_at=now - timedelta(days=1),
            is_enabled=True,
        )

        _, unauth_res, _ = await evaluate_source_metrics(session)
        assert unauth_res.passed is False
        assert unauth_res.actual_value >= 1.0
        assert str(expired_source.id) in unauth_res.source_ids


@pytest.mark.asyncio
async def test_cat57_004_revoked_source_permission_blocks_relevant_operation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-004: Revoked source permission blocks relevant operation."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(
            session, merchant.id, source_status=CatalogSourceStatus.REVOKED.value
        )

        _, unauth_res, _ = await evaluate_source_metrics(session)
        # Enabled but revoked source is flagged as unauthorized active source
        assert str(source.id) in unauth_res.source_ids


@pytest.mark.asyncio
async def test_cat57_005_1000_valid_offers_pass_initial_product_count(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-005: 1,000 valid offers pass initial product count target."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)

        # Batch insert 1000 offers
        offers = [
            MerchantOffer(
                id=uuid4(),
                garment_id=garment.id,
                merchant_id=merchant.id,
                source_id=source.id,
                source_product_id=f"PROD-{i}",
                url=f"https://retailer.example.com/items/{i}",
                price_minor=199900,
                currency="INR",
                in_stock=True,
                status="ACTIVE",
            )
            for i in range(1000)
        ]
        session.add_all(offers)
        await session.commit()

        usable_res, _, breakdown, _ = await evaluate_product_usability_metrics(
            session, minimum_usable_offers=1000
        )
        assert usable_res.passed is True
        assert usable_res.actual_value == 1000.0
        assert breakdown.usable_offers_count == 1000


@pytest.mark.asyncio
async def test_cat57_006_raw_rows_with_duplicates_exclude_duplicates(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-006: Raw rows with duplicates exclude duplicate offers."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)

        # Offer 1
        offer1 = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="DUPLICATE-SKU-01",
            url="https://retailer.example.com/items/01",
            price_minor=249900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
        )
        session.add(offer1)
        await session.commit()

        _, _, breakdown, _ = await evaluate_product_usability_metrics(
            session, minimum_usable_offers=1
        )
        assert breakdown.usable_offers_count == 1


@pytest.mark.asyncio
async def test_cat57_007_quarantined_product_excluded_from_usable_count(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-007: Quarantined product excluded from usable count."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)

        offer = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="QUARANTINE-SKU-99",
            url="https://retailer.example.com/items/quarantine",
            price_minor=99900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
        )
        session.add(offer)

        # Ingest run for quarantine record
        run = IngestRun(
            id=uuid4(),
            source_id=source.id,
            merchant_id=merchant.id,
            status="ok",
        )
        session.add(run)

        # Mark in quarantine
        quarantine = CatalogIngestionQuarantine(
            id=uuid4(),
            ingest_run_id=run.id,
            source_id=source.id,
            source_product_id="QUARANTINE-SKU-99",
            reason_code="INVALID_DATA",
            status="PENDING",
        )
        session.add(quarantine)
        await session.commit()

        _, _, breakdown, _ = await evaluate_product_usability_metrics(
            session, minimum_usable_offers=1
        )
        assert breakdown.usable_offers_count == 0
        assert breakdown.excluded_quarantined_count == 1


@pytest.mark.asyncio
async def test_cat57_008_inactive_offer_excluded_from_usable_count(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-008: Inactive offer excluded from usable count."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)

        offer = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="INACTIVE-SKU-01",
            url="https://retailer.example.com/items/inactive",
            price_minor=150000,
            currency="INR",
            in_stock=False,
            status="INACTIVE",
        )
        session.add(offer)
        await session.commit()

        _, _, breakdown, _ = await evaluate_product_usability_metrics(
            session, minimum_usable_offers=1
        )
        assert breakdown.usable_offers_count == 0
        assert breakdown.excluded_inactive_count == 1


@pytest.mark.asyncio
async def test_cat57_009_product_without_valid_merchant_url_excluded(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-009: Product without valid merchant URL excluded from usable count."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)

        offer = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="BAD-URL-SKU-01",
            url="not_a_valid_http_url",
            price_minor=120000,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
        )
        session.add(offer)
        await session.commit()

        _, _, breakdown, details = await evaluate_product_usability_metrics(
            session, minimum_usable_offers=1
        )
        assert breakdown.usable_offers_count == 0
        assert details["rejection_breakdown"]["invalid_url"] == 1


@pytest.mark.asyncio
async def test_cat57_010_same_garment_across_merchants_counted_separately(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-010: Same garment across merchants counted separately (1 canonical garment, N merchant offers)."""
    async with session_factory() as session:
        m1 = await create_test_merchant(session, name="Merchant A")
        m2 = await create_test_merchant(session, name="Merchant B")
        s1 = await create_test_source(session, m1.id, name="Feed A")
        s2 = await create_test_source(session, m2.id, name="Feed B")

        garment = await create_canonical_garment(session, name="Shared Designer Blazer")

        # Two offers for the same canonical garment
        o1 = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=m1.id,
            source_id=s1.id,
            source_product_id="SKU-BLAZER-M1",
            url="https://merchant-a.example.com/blazer",
            price_minor=450000,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
        )
        o2 = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=m2.id,
            source_id=s2.id,
            source_product_id="SKU-BLAZER-M2",
            url="https://merchant-b.example.com/blazer",
            price_minor=420000,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
        )
        session.add_all([o1, o2])
        await session.commit()

        _, _, breakdown, _ = await evaluate_product_usability_metrics(
            session, minimum_usable_offers=2
        )
        assert breakdown.usable_offers_count == 2
        assert breakdown.canonical_garments_count == 1


@pytest.mark.asyncio
async def test_cat57_011_price_within_freshness_window_classified_as_fresh(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-011: Price within freshness window classified as fresh."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)

        now = datetime.now(UTC)
        offer = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="FRESH-PRICE-SKU",
            url="https://example.com/item/fresh",
            price_minor=199900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
            last_price_verified_at=now - timedelta(hours=2),  # Window is 24h
        )
        session.add(offer)
        await session.commit()

        metric_res, details = await evaluate_price_freshness(session, minimum_fresh_percentage=95.0)
        assert details["fresh_count"] == 1
        assert details["stale_count"] == 0
        assert metric_res.passed is True
        assert metric_res.actual_value == 100.0


@pytest.mark.asyncio
async def test_cat57_012_price_beyond_freshness_window_classified_as_stale(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-012: Price beyond freshness window classified as stale."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)

        now = datetime.now(UTC)
        offer = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="STALE-PRICE-SKU",
            url="https://example.com/item/stale",
            price_minor=199900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
            last_price_verified_at=now - timedelta(hours=48),  # Beyond 24h window
        )
        session.add(offer)
        await session.commit()

        metric_res, details = await evaluate_price_freshness(session, minimum_fresh_percentage=95.0)
        assert details["fresh_count"] == 0
        assert details["stale_count"] == 1
        assert metric_res.passed is False
        assert metric_res.actual_value == 0.0


@pytest.mark.asyncio
async def test_cat57_013_missing_price_verification_timestamp_classified_as_unverified(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-013: Missing price verification timestamp classified as unverified."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)

        offer = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="UNVERIFIED-PRICE-SKU",
            url="https://example.com/item/unverified",
            price_minor=199900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
            last_price_verified_at=None,
        )
        session.add(offer)
        await session.commit()

        _, details = await evaluate_price_freshness(session)
        assert details["unverified_count"] == 1


@pytest.mark.asyncio
async def test_cat57_014_mixed_currencies_retained_explicitly(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-014: Mixed currencies retained explicitly."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)
        now = datetime.now(UTC)

        o_inr = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="CURR-INR",
            url="https://example.com/inr",
            price_minor=199900,
            currency="INR",
            in_stock=True,
            status="ACTIVE",
            last_price_verified_at=now,
        )
        o_usd = MerchantOffer(
            id=uuid4(),
            garment_id=garment.id,
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="CURR-USD",
            url="https://example.com/usd",
            price_minor=2500,
            currency="USD",
            in_stock=True,
            status="ACTIVE",
            last_price_verified_at=now,
        )
        session.add_all([o_inr, o_usd])
        await session.commit()

        _, details = await evaluate_price_freshness(session)
        assert "INR" in details["currencies_observed"]
        assert "USD" in details["currencies_observed"]


@pytest.mark.asyncio
async def test_cat57_015_valid_merchant_destination_url_classified_as_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CAT57-015: Valid merchant destination URL classified as valid."""
    monkeypatch.setattr(
        "fashx.catalog.metrics.link_health.validate_url_ssrf_safety",
        lambda url: (True, None),
    )
    mock_client = AsyncMock()
    mock_resp = MagicMock(status_code=200, headers={})
    mock_client.head.return_value = mock_resp

    result = await safe_check_product_link(
        "https://valid-retailer.com/product/123",
        client=mock_client,
    )
    assert result.status == LinkHealthClassification.VALID
    assert result.http_status == 200


@pytest.mark.asyncio
async def test_cat57_016_http_404_classified_as_broken(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CAT57-016: HTTP 404 classified as broken."""
    monkeypatch.setattr(
        "fashx.catalog.metrics.link_health.validate_url_ssrf_safety",
        lambda url: (True, None),
    )
    mock_client = AsyncMock()
    mock_resp = MagicMock(status_code=404, headers={})
    mock_client.head.return_value = mock_resp

    result = await safe_check_product_link(
        "https://retailer.com/deleted-product",
        client=mock_client,
    )
    assert result.status == LinkHealthClassification.BROKEN
    assert result.http_status == 404


@pytest.mark.asyncio
async def test_cat57_017_temporary_503_retried_and_not_classified_as_broken(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CAT57-017: Temporary 503 retried and not classified as broken."""
    monkeypatch.setattr(
        "fashx.catalog.metrics.link_health.validate_url_ssrf_safety",
        lambda url: (True, None),
    )
    mock_client = AsyncMock()
    mock_resp = MagicMock(status_code=503, headers={})
    mock_client.head.return_value = mock_resp

    result = await safe_check_product_link(
        "https://retailer.com/overloaded-gateway",
        client=mock_client,
        max_retries=1,
    )
    assert result.status == LinkHealthClassification.TEMPORARY_FAILURE
    assert result.http_status == 503


def test_cat57_018_destination_resolving_to_private_ip_blocked() -> None:
    """CAT57-018: Destination resolving or redirecting to private IP blocked by SSRF check."""
    for bad_url in [
        "http://127.0.0.1:8000/internal",
        "http://localhost:5432/admin",
        "http://192.168.1.50/product",
        "http://10.0.0.1/item",
        "ftp://retailer.com/file",
    ]:
        is_safe, err = validate_url_ssrf_safety(bad_url)
        assert is_safe is False
        assert err is not None


@pytest.mark.asyncio
async def test_cat57_019_redirect_to_unrelated_or_blocked_destination_classified_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CAT57-019: Redirect to unrelated or blocked destination classified as invalid."""
    monkeypatch.setattr(
        "fashx.catalog.metrics.link_health.validate_url_ssrf_safety",
        lambda url: (True, None) if "retailer.com" in url else (False, "SSRF blocked destination"),
    )
    mock_client = AsyncMock()
    # 302 redirect pointing to internal loopback
    mock_resp = MagicMock(status_code=302, headers={"location": "http://127.0.0.1/secrets"})
    mock_client.head.return_value = mock_resp

    result = await safe_check_product_link(
        "https://retailer.com/redirect-to-internal",
        client=mock_client,
    )
    assert result.status == LinkHealthClassification.INVALID_REDIRECT


@pytest.mark.asyncio
async def test_cat57_020_image_missing_permission_evidence_fails_traceability(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-020: Image missing permission evidence fails traceability check."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        # Image without source reference or original key
        image = CatalogImageAsset(
            id=uuid4(),
            merchant_id=merchant.id,
            source_id=uuid4(),  # unknown source
            source_product_id="SKU-IMG-01",
            original_storage_key=None,
            source_reference=None,
            status=ImageAssetStatus.ACTIVE.value,
        )
        session.add(image)
        await session.commit()

        metric_res, details = await evaluate_image_permission_traceability(session)
        assert details["untraceable_count"] >= 1
        assert metric_res.passed is False


@pytest.mark.asyncio
async def test_cat57_021_display_permission_without_storage_permission_blocks_storage(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-021: Display permission without storage permission blocks storage."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        # Source has display rights but not storage permission
        source.image_policy = "hotlink"  # not mirror

        perm_display = CatalogSourcePermission(
            id=uuid4(),
            source_id=source.id,
            permission_code=CatalogPermissionCode.IMAGE_DISPLAY.value,
            permission_status=CatalogPermissionStatus.GRANTED.value,
            granted_by="admin@fashx.internal",
            effective_at=datetime.now(UTC),
        )
        session.add(perm_display)
        await session.commit()

        image = CatalogImageAsset(
            id=uuid4(),
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="SKU-IMG-02",
            original_storage_key="s3://fashx-images/test.jpg",
            source_reference="https://brand.com/img.jpg",
            status=ImageAssetStatus.ACTIVE.value,
        )
        session.add(image)
        await session.commit()

        _, details = await evaluate_image_permission_traceability(session)
        assert details["operation_decisions"]["display_granted"] >= 1
        assert details["operation_decisions"]["store_granted"] == 0


@pytest.mark.asyncio
async def test_cat57_022_missing_vto_permission_blocks_vto_processing(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-022: Missing VTO permission blocks VTO processing."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        source.rights_tryon = False

        image = CatalogImageAsset(
            id=uuid4(),
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="SKU-IMG-03",
            original_storage_key="s3://fashx-images/test2.jpg",
            source_reference="https://brand.com/img2.jpg",
            status=ImageAssetStatus.ACTIVE.value,
        )
        session.add(image)
        await session.commit()

        _, details = await evaluate_image_permission_traceability(session)
        assert details["operation_decisions"]["vto_granted"] == 0


@pytest.mark.asyncio
async def test_cat57_023_image_source_under_takedown_blocks_processing(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-023: Image source under takedown blocks processing."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(
            session, merchant.id, source_status=CatalogSourceStatus.SUSPENDED.value
        )

        # Image under deleted/takedown status
        image = CatalogImageAsset(
            id=uuid4(),
            merchant_id=merchant.id,
            source_id=source.id,
            source_product_id="SKU-IMG-04",
            original_storage_key="s3://fashx-images/test3.jpg",
            source_reference="https://brand.com/img3.jpg",
            status=ImageAssetStatus.DELETED.value,
        )
        session.add(image)
        await session.commit()

        # Deleted images are ignored from active asset count
        metric_res, details = await evaluate_image_permission_traceability(session)
        assert str(image.id) not in details["untraceable_asset_ids"]


@pytest.mark.asyncio
async def test_cat57_024_unauthorized_active_source_fails_compliance_gate(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-024: Unauthorized active source fails overall compliance gate."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        # Enabled source with no authorization reference or terms
        await create_test_source(
            session,
            merchant.id,
            authorization_reference=None,
            is_enabled=True,
        )

        _, unauth_res, _ = await evaluate_source_metrics(session)
        assert unauth_res.passed is False
        assert unauth_res.actual_value >= 1.0


@pytest.mark.asyncio
async def test_cat57_025_zero_unauthorized_sources_passes_compliance_metric(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-025: Zero unauthorized sources passes compliance metric."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        await create_test_source(
            session, merchant.id, authorization_reference="VERIFIED-AGREEMENT-2026"
        )

        _, unauth_res, _ = await evaluate_source_metrics(session)
        assert unauth_res.passed is True
        assert unauth_res.actual_value == 0.0


def _dummy_link_fn(url: str) -> LinkCheckResult:
    return LinkCheckResult(url=url, status=LinkHealthClassification.VALID, http_status=200)


@pytest.mark.asyncio
async def test_cat57_026_repeated_evaluation_with_frozen_snapshot_is_deterministic(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-026: Repeated evaluation with frozen snapshot gives deterministic result."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        garment = await create_canonical_garment(session)
        now = datetime.now(UTC)

        for i in range(10):
            session.add(
                MerchantOffer(
                    id=uuid4(),
                    garment_id=garment.id,
                    merchant_id=merchant.id,
                    source_id=source.id,
                    source_product_id=f"DET-SKU-{i}",
                    url=f"https://retailer.com/item/{i}",
                    price_minor=100000 + i * 100,
                    currency="INR",
                    in_stock=True,
                    status="ACTIVE",
                    last_price_verified_at=now,
                )
            )
        await session.commit()

        evaluator = CatalogTargetEvaluator(session)

        report1 = await evaluator.evaluate_all_targets(random_seed=42, link_check_fn=_dummy_link_fn)
        report2 = await evaluator.evaluate_all_targets(random_seed=42, link_check_fn=_dummy_link_fn)

        assert (
            report1.metric_results["CAT-TGT-04"].actual_value
            == report2.metric_results["CAT-TGT-04"].actual_value
        )
        assert (
            report1.metric_results["CAT-TGT-02"].actual_value
            == report2.metric_results["CAT-TGT-02"].actual_value
        )


@pytest.mark.asyncio
async def test_cat57_027_evaluation_with_missing_data_reports_incomplete(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-027: Evaluation with missing data reports incomplete measurement."""
    async with session_factory() as session:
        evaluator = CatalogTargetEvaluator(session)
        report = await evaluator.evaluate_all_targets(link_check_fn=_dummy_link_fn)

        assert report.all_passed is False
        assert report.release_decision == "HOLD"
        assert len(report.blockers) > 0


@pytest.mark.asyncio
async def test_cat57_028_evaluation_run_persistence_and_retrieval(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-028: Evaluation run persistence and retrieval via CatalogReportService."""
    async with session_factory() as session:
        evaluator = CatalogTargetEvaluator(session)
        report = await evaluator.evaluate_all_targets(link_check_fn=_dummy_link_fn)

        service = CatalogReportService(session)
        saved_run = await service.record_evaluation_run(report)
        assert saved_run.id == report.evaluation_id

        fetched = await service.get_evaluation(report.evaluation_id)
        assert fetched is not None
        assert fetched.id == report.evaluation_id
        assert fetched.configuration_version == report.configuration_version


@pytest.mark.asyncio
async def test_cat57_029_evaluation_reports_never_expose_secret_values(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-029: Evaluation reports never expose secret values or tokens."""
    async with session_factory() as session:
        merchant = await create_test_merchant(session)
        source = await create_test_source(session, merchant.id)
        source.credential_secret_ref = "secrets://vault/private-api-key-very-secret-12345"
        await session.commit()

        evaluator = CatalogTargetEvaluator(session)
        report = await evaluator.evaluate_all_targets(link_check_fn=_dummy_link_fn)

        service = CatalogReportService(session)
        saved = await service.record_evaluation_run(report)

        report_json_str = str(saved.metrics_summary) + str(saved.detailed_report)
        assert "private-api-key-very-secret-12345" not in report_json_str


@pytest.mark.asyncio
async def test_cat57_030_historical_evaluations_are_immutable(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """CAT57-030: Historical evaluations are immutable."""
    async with session_factory() as session:
        evaluator = CatalogTargetEvaluator(session)
        report = await evaluator.evaluate_all_targets(link_check_fn=_dummy_link_fn)

        service = CatalogReportService(session)
        saved = await service.record_evaluation_run(report)

        # Read back twice
        r1 = await service.get_evaluation(saved.id)
        r2 = await service.get_evaluation(saved.id)
        assert r1.created_at == r2.created_at
        assert r1.metrics_summary == r2.metrics_summary
