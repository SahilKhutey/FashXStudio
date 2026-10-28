from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from fashx.application.erasure import erase_account
from fashx.core.dependencies import get_tryon_adapter
from fashx.core.settings import Settings, get_settings
from fashx.health.router import evaluate_readiness
from fashx.main import app
from fashx.security.deps import get_identity_repo
from fashx.security.identity import InMemoryIdentityRepo
from fashx.workers.app import (
    enrich_garment_task,
    ingest_catalog_feed,
    process_tryon_job,
    relay_outbox_events,
    run_retention_jobs,
    sweep_storage_erasure,
)
from tests.conftest import make_token


def test_settings_fail_fast_canonical_production() -> None:
    """Verify that canonical production flag gates all strict environment validations."""
    # 1. APP_ENV=production without ENV=prod must fail fast
    with pytest.raises(ValidationError, match="Production requires ENV=prod"):
        Settings(APP_ENV="production", ENV="dev")

    # 2. Production refuses in-memory repository backend
    with pytest.raises(ValidationError, match="prod requires REPO_BACKEND=sql"):
        Settings(
            ENV="prod",
            APP_ENV="production",
            REPO_BACKEND="memory",
            STORAGE_BACKEND="s3",
            S3_BUCKET="bucket",
            S3_USE_IAM_ROLE=True,
            AUTH_MODE="jwks",
            AUTH_JWKS_URL="https://auth.example.com/jwks.json",
            TRYON_PROVIDER="fashn_api",
            FASHN_API_KEY="secret-key",
            PRIVACY_URL="https://example.com/privacy",
            TERMS_URL="https://example.com/terms",
            CORS_ORIGINS=["https://app.example.com"],
        )

    # 3. Production refuses local storage backend
    with pytest.raises(ValidationError, match="prod requires STORAGE_BACKEND=s3"):
        Settings(
            ENV="prod",
            APP_ENV="production",
            REPO_BACKEND="sql",
            STORAGE_BACKEND="local",
            AUTH_MODE="jwks",
            AUTH_JWKS_URL="https://auth.example.com/jwks.json",
            TRYON_PROVIDER="fashn_api",
            FASHN_API_KEY="secret-key",
            PRIVACY_URL="https://example.com/privacy",
            TERMS_URL="https://example.com/terms",
            CORS_ORIGINS=["https://app.example.com"],
        )

    # 4. Production refuses mock try-on provider
    with pytest.raises(ValidationError, match="prod requires non-mock TRYON_PROVIDER"):
        Settings(
            ENV="prod",
            APP_ENV="production",
            REPO_BACKEND="sql",
            STORAGE_BACKEND="s3",
            S3_BUCKET="bucket",
            S3_USE_IAM_ROLE=True,
            AUTH_MODE="jwks",
            AUTH_JWKS_URL="https://auth.example.com/jwks.json",
            TRYON_PROVIDER="mock",
            PRIVACY_URL="https://example.com/privacy",
            TERMS_URL="https://example.com/terms",
            CORS_ORIGINS=["https://app.example.com"],
        )

    # 5. Production refuses wildcard CORS
    with pytest.raises(ValidationError, match="wildcard CORS not allowed in prod"):
        Settings(
            ENV="prod",
            APP_ENV="production",
            REPO_BACKEND="sql",
            STORAGE_BACKEND="s3",
            S3_BUCKET="bucket",
            S3_USE_IAM_ROLE=True,
            AUTH_MODE="jwks",
            AUTH_JWKS_URL="https://auth.example.com/jwks.json",
            TRYON_PROVIDER="fashn_api",
            FASHN_API_KEY="secret-key",
            PRIVACY_URL="https://example.com/privacy",
            TERMS_URL="https://example.com/terms",
            CORS_ORIGINS=["*"],
        )

    # 6. Valid production profile passes and sets is_production=True
    valid_prod = Settings(
        ENV="prod",
        APP_ENV="production",
        REPO_BACKEND="sql",
        STORAGE_BACKEND="s3",
        S3_BUCKET="fashx-prod-media",
        S3_USE_IAM_ROLE=True,
        AUTH_MODE="jwks",
        AUTH_JWKS_URL="https://auth.example.com/jwks.json",
        TRYON_PROVIDER="fashn_api",
        FASHN_API_KEY="verified-secret-key",
        PRIVACY_URL="https://example.com/privacy",
        TERMS_URL="https://example.com/terms",
        CORS_ORIGINS=["https://app.example.com"],
    )
    assert valid_prod.is_production is True
    assert valid_prod.env == "prod"


def test_tryon_adapter_resolution_refuses_unimplemented_selfhost(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure get_tryon_adapter raises NotImplementedError for fashn_selfhost instead of falling back to mock."""
    get_settings.cache_clear()
    monkeypatch.setenv("TRYON_PROVIDER", "fashn_selfhost")
    try:
        with pytest.raises(NotImplementedError, match="fashn_selfhost try-on adapter is not implemented"):
            get_tryon_adapter()
    finally:
        get_settings.cache_clear()


def test_worker_tryon_job_retry_on_transient_error() -> None:
    """Verify that process_tryon_job task invokes retry upon unexpected transient exception."""
    job_id = uuid4()
    with patch.object(process_tryon_job, "retry", side_effect=RuntimeError("Retry triggered")) as mock_retry:
        with patch("fashx.workers.app.run_tryon_job", side_effect=ConnectionError("Redis timeout")):
            with pytest.raises(RuntimeError, match="Retry triggered"):
                process_tryon_job.run(str(job_id))
            mock_retry.assert_called_once()


def test_worker_ingest_feed_verifies_source_cleared() -> None:
    """Verify ingest_catalog_feed checks source existence and clearance."""
    source_id = uuid4()

    mock_source = MagicMock()
    mock_source.status = "unapproved"
    mock_source.rights_display = False
    mock_source.rights_tryon = False

    with patch("fashx.workers.app.get_session_factory") as mock_sf:
        mock_uow = MagicMock()
        mock_uow.sources.get_by_id = AsyncMock(return_value=mock_source)
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)

        with patch("fashx.catalog.repositories.catalog_repository.CatalogUnitOfWork", return_value=mock_uow):
            result = ingest_catalog_feed(str(source_id))
            assert result["status"] == "rejected"
            assert "not cleared" in result["reason"]


def test_worker_enrich_garment_task_execution() -> None:
    """Verify enrich_garment_task invokes EnrichGarmentUseCase with valid UUID."""
    garment_id = uuid4()

    mock_result = MagicMock()
    mock_result.garment_id = garment_id
    mock_result.garment_version = 2
    mock_result.model_version = "vlm-v1"

    with patch("fashx.workers.app.get_session_factory"):
        with patch("fashx.catalog.repositories.catalog_repository.CatalogUnitOfWork"):
            with patch("fashx.catalog.application.enrich_garment.EnrichGarmentUseCase") as mock_uc_cls:
                mock_uc = MagicMock()
                mock_uc.execute = AsyncMock(return_value=mock_result)
                mock_uc_cls.return_value = mock_uc

                res = enrich_garment_task(str(garment_id))
                assert res["status"] == "enriched"
                assert res["garment_version"] == 2


def test_worker_outbox_relay_and_erasure_sweeps() -> None:
    """Verify relay_outbox_events and sweep_storage_erasure call run_outbox_worker_once."""
    with patch("fashx.workers.app.get_session_factory") as mock_sf:
        mock_session = AsyncMock()
        mock_sf.return_value.__aenter__.return_value = mock_session
        mock_sf.return_value.__aexit__.return_value = None

        with patch("fashx.workers.app.get_storage"):
            with patch("fashx.integration.outbox.run_outbox_worker_once", new_callable=AsyncMock) as mock_outbox:
                mock_outbox.return_value = 5

                relay_res = relay_outbox_events()
                assert relay_res["status"] == "relayed"
                assert relay_res["processed"] == 5

                sweep_res = sweep_storage_erasure()
                assert sweep_res["status"] == "erasure_sweep_complete"
                assert sweep_res["keys_purged"] == 5


def test_worker_retention_job_execution() -> None:
    """Verify run_retention_jobs triggers daily retention cleanup."""
    with patch("fashx.workers.app.get_session_factory") as mock_sf:
        mock_session = AsyncMock()
        mock_sf.return_value.__aenter__.return_value = mock_session
        mock_sf.return_value.__aexit__.return_value = None

        with patch("fashx.workers.app.get_storage"):
            with patch("fashx.application.retention.run_daily_retention", new_callable=AsyncMock) as mock_ret:
                mock_ret.return_value = {
                    "status": "success",
                    "tryon_jobs_deleted": 3,
                    "storage_keys_purged": 6,
                    "impressions_deleted": 50,
                    "analytics_events_anonymized": 10,
                }

                res = run_retention_jobs()
                assert res["status"] == "success"
                assert res["tryon_jobs_deleted"] == 3


@pytest.mark.asyncio
async def test_readiness_reports_503_on_dependency_failure() -> None:
    """Verify evaluate_readiness reports degraded and overall failure when database fails."""
    with patch("fashx.health.router.check_database", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = False
        with patch("fashx.health.router.check_redis_dependency", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = True
            with patch("fashx.health.router.check_jwks_dependency", new_callable=AsyncMock) as mock_jwks:
                mock_jwks.return_value = True

                with patch("fashx.health.router.get_settings") as mock_settings:
                    s = Settings(readiness_requires_database=True)
                    mock_settings.return_value = s

                    all_ok, deps = await evaluate_readiness()
                    assert all_ok is False
                    assert deps["postgres"] == "degraded"
                    assert deps["redis"] == "ok"


@pytest.mark.asyncio
async def test_account_erasure_workflow() -> None:
    """Verify erase_account cascades biometrics, enqueues storage purges, and records tombstones."""
    user_id = uuid4()
    mock_uow = MagicMock()
    mock_session = AsyncMock()
    mock_session.expunge_all = MagicMock()
    mock_uow.session = mock_session
    mock_uow.outbox = MagicMock()
    mock_uow.outbox.add = AsyncMock()
    mock_uow.media = MagicMock()
    mock_uow.media.list_for_user = AsyncMock(return_value=[])
    mock_uow.photos = MagicMock()
    mock_uow.photos.list_for_user = AsyncMock(return_value=[])

    mock_storage = MagicMock()

    result = await erase_account(uow=mock_uow, user_id=user_id, storage=mock_storage)
    assert result["user_id"] == str(user_id)
    assert result["status"] == "account_erased"
    assert mock_uow.outbox.add.called
    assert mock_storage.delete_prefix.called


def test_cross_user_isolation_blocks_unauthorized_access() -> None:
    """Verify that User B cannot access User A's private resources."""
    identity_repo = InMemoryIdentityRepo()
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo

    user_b_token = make_token(sub="user-b")

    client_b = TestClient(app, headers={"Authorization": f"Bearer {user_b_token}"})

    # User B attempting to access User A's wardrobe items
    user_a_uuid = uuid4()
    res = client_b.get(f"/api/v1/wardrobe/users/{user_a_uuid}")
    # Must fail closed with 403 or 404
    assert res.status_code in (403, 404)
