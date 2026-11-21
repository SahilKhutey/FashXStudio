"""Unit tests for catalog ingestion authorization (ING-001 to ING-006, ING-031, ING-037)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_auth import (
    CatalogAuthorizationEvidence,
    CatalogPermissionCode,
    CatalogSourcePermission,
)
from fashx.catalog.acquisition.contract import AcquisitionBatch, SourceProduct
from fashx.catalog.acquisition.pipeline import AcquisitionPipeline
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork


@pytest.mark.asyncio
async def test_ing_001_registered_active_source_accepted(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-001: Registered active source with granted permissions is accepted."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)

    batch = AcquisitionBatch(
        source_slug=setup_authorized_source["source_slug"],
        products=[
            SourceProduct(
                source_slug=setup_authorized_source["source_slug"],
                source_product_id="PROD-001",
                title="Cotton Polo Shirt",
                category="tops",
                subcategory="tshirt",
                price_minor=99900,
                currency="INR",
                product_url="https://merchant.example.com/polo-1",
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is True
    assert report.status == "COMPLETED"
    assert report.inserted == 1
    assert report.rejected == 0


@pytest.mark.asyncio
async def test_ing_002_unknown_source_rejected(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """ING-002: Unknown source ID/slug is rejected before processing."""
    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)

    batch = AcquisitionBatch(
        source_slug="nonexistent-source",
        products=[
            SourceProduct(
                source_slug="nonexistent-source",
                source_product_id="PROD-002",
                title="Sample Shirt",
                category="tops",
                price_minor=1000,
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.status == "REJECTED"
    assert any("unregistered_source" in k for k in report.rejection_reasons)


@pytest.mark.asyncio
async def test_ing_003_merchant_not_verified_rejected(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """ING-003: Ingestion from an unverified or rejected merchant is rejected."""
    async with session_factory() as session:
        merchant = Merchant(
            id=uuid4(),
            name="Rejected Merchant",
            merchant_type="retailer",
            verification_status="REJECTED",
        )
        session.add(merchant)
        source = CatalogSource(
            id=uuid4(),
            merchant_id=merchant.id,
            slug=f"rejected-merchant-source-{uuid4().hex[:6]}",
            name="Rejected Source",
            kind="feed_url",
            source_status="ACTIVE",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
        )
        session.add(source)
        await session.commit()
        source_slug = source.slug

    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    batch = AcquisitionBatch(
        source_slug=source_slug,
        products=[
            SourceProduct(
                source_slug=source_slug,
                source_product_id="PROD-003",
                title="Casual Trousers",
                category="bottoms",
                price_minor=129900,
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.status == "REJECTED"
    assert "merchant_not_verified" in report.rejection_reasons


@pytest.mark.asyncio
async def test_ing_004_source_suspended_rejected(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """ING-004: Ingestion from a suspended source is rejected immediately."""
    async with session_factory() as session:
        merchant = Merchant(
            id=uuid4(),
            name="Suspended Merchant",
            merchant_type="retailer",
            verification_status="VERIFIED",
        )
        session.add(merchant)
        source = CatalogSource(
            id=uuid4(),
            merchant_id=merchant.id,
            slug=f"suspended-source-{uuid4().hex[:6]}",
            name="Suspended Source",
            kind="feed_url",
            source_status="SUSPENDED",
            status="suspended",
            rights_display=False,
            rights_tryon=False,
        )
        session.add(source)
        await session.commit()
        source_slug = source.slug

    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    batch = AcquisitionBatch(
        source_slug=source_slug,
        products=[
            SourceProduct(
                source_slug=source_slug,
                source_product_id="PROD-004",
                title="Linen Shirt",
                category="tops",
                price_minor=149900,
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.status == "REJECTED"
    assert "source_suspended" in report.rejection_reasons


@pytest.mark.asyncio
async def test_ing_005_expired_source_rejected(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """ING-005: Ingestion from an expired source is rejected."""
    async with session_factory() as session:
        merchant = Merchant(
            id=uuid4(),
            name="Expired Merchant",
            merchant_type="retailer",
            verification_status="VERIFIED",
        )
        session.add(merchant)
        source = CatalogSource(
            id=uuid4(),
            merchant_id=merchant.id,
            slug=f"expired-source-{uuid4().hex[:6]}",
            name="Expired Source",
            kind="feed_url",
            source_status="EXPIRED",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        session.add(source)
        await session.commit()
        source_slug = source.slug

    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    batch = AcquisitionBatch(
        source_slug=source_slug,
        products=[
            SourceProduct(
                source_slug=source_slug,
                source_product_id="PROD-005",
                title="Denim Jacket",
                category="outerwear",
                price_minor=249900,
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.status == "REJECTED"
    assert "source_expired" in report.rejection_reasons


@pytest.mark.asyncio
async def test_ing_006_product_data_storage_denied_aborts_persistence(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """ING-006: When PRODUCT_DATA_STORE is denied, records are not persisted."""
    async with session_factory() as session:
        merchant = Merchant(
            id=uuid4(),
            name="No Store Merchant",
            merchant_type="retailer",
            verification_status="VERIFIED",
        )
        session.add(merchant)
        source = CatalogSource(
            id=uuid4(),
            merchant_id=merchant.id,
            slug=f"no-store-source-{uuid4().hex[:6]}",
            name="No Store Source",
            kind="feed_url",
            source_status="ACTIVE",
            status="cleared",
            rights_display=True,
            rights_tryon=False,
        )
        session.add(source)

        evidence = CatalogAuthorizationEvidence(
            id=uuid4(),
            source_id=source.id,
            evidence_type="CONTRACT",
            document_reference="s3://contracts/test.pdf",
            document_sha256="abc1234567890123456789012345678901234567890123456789012345678901",
            agreement_reference="TEST-006",
            agreement_version="1.0",
            granted_by_name="Legal",
            granted_by_role="Counsel",
            verification_status="VERIFIED",
        )
        session.add(evidence)

        # Grant READ but NOT STORE
        perm = CatalogSourcePermission(
            source_id=source.id,
            permission_code=CatalogPermissionCode.PRODUCT_DATA_READ.value,
            permission_status="GRANTED",
            granted_by="founder@fashx.internal",
            evidence_id=evidence.id,
            effective_at=datetime.now(UTC),
        )
        session.add(perm)
        await session.commit()
        source_slug = source.slug

    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    batch = AcquisitionBatch(
        source_slug=source_slug,
        products=[
            SourceProduct(
                source_slug=source_slug,
                source_product_id="PROD-006",
                title="Cotton Kurta",
                category="tops",
                price_minor=129900,
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.status == "REJECTED"
    assert any("permission_denied" in k for k in report.rejection_reasons)


@pytest.mark.asyncio
async def test_ing_031_permission_revoked_mid_run_aborts_safely(
    session_factory: async_sessionmaker[AsyncSession],
    setup_authorized_source: dict,
) -> None:
    """ING-031: If source permission is revoked, sensitive operations abort."""
    # Revoke permissions
    async with session_factory() as session:
        source_id = setup_authorized_source["source_id"]
        source = await session.get(CatalogSource, source_id)
        if source:
            source.source_status = "SUSPENDED"
        await session.commit()

    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    batch = AcquisitionBatch(
        source_slug=setup_authorized_source["source_slug"],
        products=[
            SourceProduct(
                source_slug=setup_authorized_source["source_slug"],
                source_product_id="REVOKED-001",
                title="Silk Saree",
                category="dresses",
                price_minor=499900,
            )
        ],
    )
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.status == "REJECTED"


@pytest.mark.asyncio
async def test_ing_037_source_merchant_mismatch_rejected(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """ING-037: Ingestion rejected if source references a non-existent or deleted merchant."""
    async with session_factory() as session:
        source = CatalogSource(
            id=uuid4(),
            merchant_id=uuid4(),  # Non-existent merchant ID
            slug=f"mismatched-source-{uuid4().hex[:6]}",
            name="Mismatched Source",
            kind="feed_url",
            source_status="ACTIVE",
            status="cleared",
        )
        session.add(source)
        await session.commit()
        source_slug = source.slug

    uow = CatalogUnitOfWork(session_factory)
    pipeline = AcquisitionPipeline(uow)
    batch = AcquisitionBatch(
        source_slug=source_slug,
        products=[
            SourceProduct(
                source_slug=source_slug,
                source_product_id="MISMATCH-001",
                title="T-Shirt",
                category="tops",
                price_minor=99900,
            )
        ],
    )
    # When merchant_id does not exist, authorization fails closed.
    report = await pipeline.process_batch(batch, apply=True)
    assert report.success is False
    assert report.status == "REJECTED"
