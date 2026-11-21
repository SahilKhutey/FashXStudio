from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CatalogSource, Merchant
from database.models.catalog_auth import (
    CatalogAuthorizationEvidence,
    CatalogPermissionCode,
    CatalogSourcePermission,
)
from tests.unit.conftest import async_engine, session_factory

__all__ = ["async_engine", "session_factory", "setup_authorized_source"]


@pytest_asyncio.fixture
async def setup_authorized_source(
    session_factory: async_sessionmaker[AsyncSession],
):
    """Fixture creating an approved merchant and source with full catalog permissions."""
    async with session_factory() as session:
        feed_name = f"Authorized Feed {uuid4().hex[:6]}"
        merchant = Merchant(
            id=uuid4(),
            name=feed_name,
            merchant_type="brand",
            legal_name="Test Merchant Ltd",
            country_code="IN",
            verification_status="VERIFIED",
        )
        session.add(merchant)

        source = CatalogSource(
            id=uuid4(),
            merchant_id=merchant.id,
            slug=f"authorized-feed-{uuid4().hex[:6]}",
            name=feed_name,
            kind="feed_url",
            source_type="FEED",
            access_method="HTTPS_FEED",
            source_status="ACTIVE",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
            market_codes=["IN"],
            category_codes=["tops", "dresses", "jackets"],
        )
        session.add(source)

        evidence = CatalogAuthorizationEvidence(
            id=uuid4(),
            source_id=source.id,
            evidence_type="CONTRACT",
            document_reference="s3://contracts/test.pdf",
            document_sha256="abc1234567890123456789012345678901234567890123456789012345678901",
            agreement_reference="TEST-REF-001",
            agreement_version="1.0",
            granted_by_name="Counsel",
            granted_by_role="Legal",
            verification_status="VERIFIED",
        )
        session.add(evidence)

        # Grant read & store permissions
        for perm_code in (
            CatalogPermissionCode.PRODUCT_DATA_READ,
            CatalogPermissionCode.PRODUCT_DATA_STORE,
            CatalogPermissionCode.IMAGE_DISPLAY,
        ):
            perm = CatalogSourcePermission(
                source_id=source.id,
                permission_code=perm_code.value,
                permission_status="GRANTED",
                granted_by="founder@fashx.internal",
                evidence_id=evidence.id,
                effective_at=datetime.now(UTC),
            )
            session.add(perm)

        await session.commit()
        return {"merchant_id": merchant.id, "source_id": source.id, "source_slug": source.slug}
