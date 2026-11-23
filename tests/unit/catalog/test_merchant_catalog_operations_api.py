from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CatalogSource,
    Merchant,
    MerchantProduct,
)
from fashx.core.database import get_db_session
from fashx.main import app
from fashx.security.deps import Principal, get_principal


@pytest.fixture
def override_db(session_factory: async_sessionmaker[AsyncSession]):
    async def _get_test_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    prev = app.dependency_overrides.get(get_db_session)
    app.dependency_overrides[get_db_session] = _get_test_session
    yield
    if prev is not None:
        app.dependency_overrides[get_db_session] = prev
    else:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
def test_client(override_db) -> TestClient:
    return TestClient(app)


def test_api_connect_merchant_source(
    test_client: TestClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    merchant_id = uuid.uuid4()

    async def _setup():
        async with session_factory() as session:
            m = Merchant(
                id=merchant_id,
                name="API Test Brand",
                merchant_type="BRAND_DIRECT",
                country_code="IN",
            )
            session.add(m)
            await session.commit()

    import asyncio

    asyncio.run(_setup())

    # Set merchant principal
    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=str(merchant_id),
        subject="merchant-user",
        roles=frozenset(["merchant_operator"]),
    )

    resp = test_client.post(
        "/api/v1/merchant/sources",
        headers={"X-Merchant-ID": str(merchant_id)},
        json={
            "merchant_id": str(merchant_id),
            "slug": f"api-test-source-{uuid.uuid4().hex[:6]}",
            "name": "API Test Source",
            "source_type": "MERCHANT_API",
            "adapter_name": "generic_merchant_api",
            "access_method": "API_KEY",
            "credential_secret_ref": "secrets://vault/keys/api-key",
            "refresh_hours": 24,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["is_enabled"] is True
    assert body["operational_status"] == "ENABLED"
    assert body["masked_credential_ref"] == "secrets://vault/keys/******"


def test_api_get_source_sync_status(
    test_client: TestClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    merchant_id = uuid.uuid4()
    source_id = uuid.uuid4()

    async def _setup():
        async with session_factory() as session:
            m = Merchant(
                id=merchant_id, name="Status Brand", merchant_type="BRAND_DIRECT", country_code="IN"
            )
            s = CatalogSource(
                id=source_id,
                merchant_id=merchant_id,
                slug=f"status-src-{uuid.uuid4().hex[:6]}",
                name="Status Source",
                kind="api",
                status="cleared",
                source_status="AUTHORIZED",
                operational_status="ENABLED",
                is_enabled=True,
            )
            session.add_all([m, s])
            await session.commit()

    import asyncio

    asyncio.run(_setup())

    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=str(merchant_id),
        subject="merchant-user",
        roles=frozenset(["merchant_operator"]),
    )

    resp = test_client.get(
        f"/api/v1/merchant/sources/{source_id}/status",
        headers={"X-Merchant-ID": str(merchant_id)},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_id"] == str(source_id)
    assert body["is_healthy"] is True


def test_api_patch_operational_status(
    test_client: TestClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    merchant_id = uuid.uuid4()
    source_id = uuid.uuid4()

    async def _setup():
        async with session_factory() as session:
            m = Merchant(
                id=merchant_id,
                name="Lifecycle Brand",
                merchant_type="BRAND_DIRECT",
                country_code="IN",
            )
            s = CatalogSource(
                id=source_id,
                merchant_id=merchant_id,
                slug=f"life-src-{uuid.uuid4().hex[:6]}",
                name="Lifecycle Source",
                kind="api",
                status="cleared",
                source_status="AUTHORIZED",
                operational_status="ENABLED",
                is_enabled=True,
            )
            session.add_all([m, s])
            await session.commit()

    import asyncio

    asyncio.run(_setup())

    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=str(merchant_id),
        subject="merchant-user",
        roles=frozenset(["merchant_operator"]),
    )

    resp = test_client.patch(
        f"/api/v1/merchant/sources/{source_id}/operational-status",
        headers={"X-Merchant-ID": str(merchant_id)},
        json={"target_status": "DISABLED", "reason": "Paused for feed catalog revamp"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_enabled"] is False
    assert body["operational_status"] == "DISABLED"


def test_api_trigger_manual_sync(
    test_client: TestClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    merchant_id = uuid.uuid4()
    source_id = uuid.uuid4()

    async def _setup():
        async with session_factory() as session:
            m = Merchant(
                id=merchant_id, name="Sync Brand", merchant_type="BRAND_DIRECT", country_code="IN"
            )
            s = CatalogSource(
                id=source_id,
                merchant_id=merchant_id,
                slug=f"sync-src-{uuid.uuid4().hex[:6]}",
                name="Sync Source",
                kind="api",
                status="cleared",
                source_status="AUTHORIZED",
                operational_status="ENABLED",
                is_enabled=True,
            )
            session.add_all([m, s])
            await session.commit()

    import asyncio

    asyncio.run(_setup())

    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=str(merchant_id),
        subject="merchant-user",
        roles=frozenset(["merchant_operator"]),
    )

    resp = test_client.post(
        f"/api/v1/merchant/sources/{source_id}/sync",
        headers={"X-Merchant-ID": str(merchant_id)},
        json={"sync_mode": "INCREMENTAL", "idempotency_key": "api-sync-01"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "queued"
    assert body["idempotency_key"] == "api-sync-01"


def test_api_product_override(
    test_client: TestClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    merchant_id = uuid.uuid4()
    source_id = uuid.uuid4()
    product_id = uuid.uuid4()

    async def _setup():
        async with session_factory() as session:
            m = Merchant(
                id=merchant_id,
                name="Override Brand",
                merchant_type="BRAND_DIRECT",
                country_code="IN",
            )
            s = CatalogSource(
                id=source_id,
                merchant_id=merchant_id,
                slug=f"ov-src-{uuid.uuid4().hex[:6]}",
                name="Override Source",
                kind="api",
                status="cleared",
            )
            p = MerchantProduct(
                id=product_id,
                merchant_id=merchant_id,
                source_id=source_id,
                source_product_id="PROD-OV-1",
                title="Basic Shirt",
                source_url="https://merchant.com/prod1",
            )
            session.add_all([m, s, p])
            await session.commit()

    import asyncio

    asyncio.run(_setup())

    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=str(merchant_id),
        subject="merchant-user",
        roles=frozenset(["merchant_operator"]),
    )

    resp = test_client.post(
        f"/api/v1/merchant/products/{product_id}/override",
        headers={"X-Merchant-ID": str(merchant_id)},
        json={
            "field_name": "title",
            "override_value": {"value": "Super Silk Designer Shirt"},
            "reason": "Editorial override",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["field_name"] == "title"
    assert body["override_value"] == {"value": "Super Silk Designer Shirt"}


def test_api_admin_source_takedown(
    test_client: TestClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    merchant_id = uuid.uuid4()
    source_id = uuid.uuid4()

    async def _setup():
        async with session_factory() as session:
            m = Merchant(
                id=merchant_id,
                name="Takedown Brand",
                merchant_type="BRAND_DIRECT",
                country_code="IN",
            )
            s = CatalogSource(
                id=source_id,
                merchant_id=merchant_id,
                slug=f"td-src-{uuid.uuid4().hex[:6]}",
                name="Takedown Source",
                kind="api",
                status="cleared",
                source_status="AUTHORIZED",
                operational_status="ENABLED",
                is_enabled=True,
            )
            session.add_all([m, s])
            await session.commit()

    import asyncio

    asyncio.run(_setup())

    # Set platform admin principal
    app.dependency_overrides[get_principal] = lambda: Principal(
        user_id=str(uuid.uuid4()),
        subject="admin-user",
        roles=frozenset(["admin"]),
    )

    resp = test_client.post(
        f"/api/v1/admin/sources/{source_id}/takedown",
        json={
            "reason_code": "LEGAL_REQUEST",
            "reason_text": "Emergency legal takedown requested by rights owner",
            "purge_images": True,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["takedown_status"] == "COMPLETED"
    assert body["source_id"] == str(source_id)
