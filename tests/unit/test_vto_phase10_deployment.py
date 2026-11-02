from __future__ import annotations

import logging
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from fashx.core.dependencies import get_tryon_adapter
from fashx.core.logging import RedactFilter, scrub
from fashx.core.settings import Settings, get_settings
from fashx.health.router import evaluate_readiness
from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter
from fashx.main import app
from fashx.workers.app import process_tryon_job


def valid_prod_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "ENV": "prod",
        "APP_ENV": "production",
        "REPO_BACKEND": "sql",
        "STORAGE_BACKEND": "s3",
        "S3_BUCKET": "fashx-media-prod",
        "S3_USE_IAM_ROLE": True,
        "AUTH_MODE": "jwks",
        "AUTH_JWKS_URL": "https://auth.example.com/.well-known/jwks.json",
        "TRYON_PROVIDER": "fashn_api",
        "FASHN_API_KEY": "test-provider-key",
        "PRIVACY_URL": "https://app.example.com/privacy",
        "TERMS_URL": "https://app.example.com/terms",
        "CORS_ORIGINS": ["https://app.example.com"],
        "ENABLE_B2B": False,
    }
    values.update(overrides)
    return Settings(**values)


# -----------------------------------------------------------------------------
# 1. Production Settings Refusal Tests
# -----------------------------------------------------------------------------


def test_production_rejects_mock_provider() -> None:
    with pytest.raises(ValidationError, match="non-mock TRYON_PROVIDER"):
        valid_prod_settings(TRYON_PROVIDER="mock")


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="wildcard CORS not allowed in prod"):
        valid_prod_settings(CORS_ORIGINS=["*"])


def test_production_requires_sql_backend() -> None:
    with pytest.raises(ValidationError, match="prod requires REPO_BACKEND=sql"):
        valid_prod_settings(REPO_BACKEND="memory")


def test_production_requires_s3_storage() -> None:
    with pytest.raises(ValidationError, match="prod requires STORAGE_BACKEND=s3"):
        valid_prod_settings(STORAGE_BACKEND="local")


def test_production_requires_s3_bucket() -> None:
    with pytest.raises(ValidationError, match="prod requires S3_BUCKET"):
        valid_prod_settings(S3_BUCKET="")


def test_production_requires_jwks_auth() -> None:
    with pytest.raises(ValidationError, match="prod requires AUTH_MODE=jwks"):
        valid_prod_settings(AUTH_MODE="local")


def test_production_requires_privacy_and_terms() -> None:
    with pytest.raises(ValidationError, match="prod requires PRIVACY_URL and TERMS_URL"):
        valid_prod_settings(PRIVACY_URL="")

    with pytest.raises(ValidationError, match="prod requires PRIVACY_URL and TERMS_URL"):
        valid_prod_settings(TERMS_URL="")


def test_production_rejects_b2b_flag() -> None:
    with pytest.raises(ValidationError, match="ENABLE_B2B must be false in prod"):
        valid_prod_settings(ENABLE_B2B=True)


def test_production_accepts_valid_configuration() -> None:
    cfg = valid_prod_settings()
    assert cfg.is_production is True
    assert cfg.env == "prod"
    assert cfg.storage_backend == "s3"
    assert cfg.s3_use_iam_role is True
    assert cfg.signed_url_ttl_s == 300


# -----------------------------------------------------------------------------
# 2. Health & Readiness Evaluator (Isolated from VTO Provider)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_readiness_evaluator_all_dependencies_healthy() -> None:
    with patch("fashx.health.router.check_database", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = True
        with patch("fashx.health.router.check_redis_dependency", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = True
            with patch("fashx.health.router.check_jwks_dependency", new_callable=AsyncMock) as mock_jwks:
                mock_jwks.return_value = True
                with patch("fashx.health.router.get_settings") as mock_settings:
                    mock_settings.return_value = valid_prod_settings()

                    all_ok, deps = await evaluate_readiness()
                    assert all_ok is True
                    assert deps["postgres"] == "ok"
                    assert deps["redis"] == "ok"
                    assert deps["jwks"] == "ok"
                    # External VTO provider is deliberately isolated from core readiness check
                    assert "tryon" not in deps
                    assert "provider" not in deps


@pytest.mark.asyncio
async def test_readiness_evaluator_reports_degraded_on_postgres_failure() -> None:
    with patch("fashx.health.router.check_database", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = False
        with patch("fashx.health.router.check_redis_dependency", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = True
            with patch("fashx.health.router.check_jwks_dependency", new_callable=AsyncMock) as mock_jwks:
                mock_jwks.return_value = True
                with patch("fashx.health.router.get_settings") as mock_settings:
                    mock_settings.return_value = valid_prod_settings()

                    all_ok, deps = await evaluate_readiness()
                    assert all_ok is False
                    assert deps["postgres"] == "degraded"
                    assert deps["redis"] == "ok"


@pytest.mark.asyncio
async def test_readiness_evaluator_reports_degraded_on_redis_failure() -> None:
    with patch("fashx.health.router.check_database", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = True
        with patch("fashx.health.router.check_redis_dependency", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = False
            with patch("fashx.health.router.check_jwks_dependency", new_callable=AsyncMock) as mock_jwks:
                mock_jwks.return_value = True
                with patch("fashx.health.router.get_settings") as mock_settings:
                    mock_settings.return_value = valid_prod_settings()

                    all_ok, deps = await evaluate_readiness()
                    assert all_ok is False
                    assert deps["postgres"] == "ok"
                    assert deps["redis"] == "degraded"


def test_healthz_live_endpoint_is_lightweight() -> None:
    """Verify /healthz/live returns 200 without connecting to Postgres or Redis."""
    client = TestClient(app)
    resp = client.get("/healthz/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"] == "not_checked"


# -----------------------------------------------------------------------------
# 3. Provider Resolution & Production Safety Gate
# -----------------------------------------------------------------------------


def test_get_tryon_adapter_resolves_fashn_api(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("TRYON_PROVIDER", "fashn_api")
    monkeypatch.setenv("FASHN_API_KEY", "real-provider-secret")
    monkeypatch.setenv("ENV", "dev")
    try:
        adapter = get_tryon_adapter()
        assert isinstance(adapter, FashnApiAdapter)
    finally:
        get_settings.cache_clear()


def test_get_tryon_adapter_refuses_unimplemented_fashn_selfhost(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("TRYON_PROVIDER", "fashn_selfhost")
    monkeypatch.setenv("ENV", "dev")
    try:
        with pytest.raises(NotImplementedError, match="fashn_selfhost try-on adapter is not implemented"):
            get_tryon_adapter()
    finally:
        get_settings.cache_clear()


# -----------------------------------------------------------------------------
# 4. Worker Resilience & Job Recovery
# -----------------------------------------------------------------------------


def test_worker_tryon_job_retry_on_redis_disconnection() -> None:
    """Verify that process_tryon_job triggers Celery retry with bounded count on transport error."""
    job_id = uuid4()
    with patch.object(process_tryon_job, "retry", side_effect=RuntimeError("Retry invoked")) as mock_retry:
        with patch("fashx.workers.app.run_tryon_job", side_effect=ConnectionError("Redis connection dropped")):
            with pytest.raises(RuntimeError, match="Retry invoked"):
                process_tryon_job.run(str(job_id))
            mock_retry.assert_called_once()


# -----------------------------------------------------------------------------
# 5. Observability, Structured Logging & PII Redaction
# -----------------------------------------------------------------------------


def test_log_redaction_scrubs_jwt_and_presigned_signatures() -> None:
    # 1. Bearer JWT
    sample_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakThisSignature"
    message_with_jwt = f"User authenticated with {sample_jwt}"
    scrubbed = scrub(message_with_jwt)
    assert sample_jwt not in scrubbed
    assert "[redacted]" in scrubbed

    # 2. S3 Presigned URL Signature
    sample_url = "https://fashx-media-prod.s3.ap-south-1.amazonaws.com/u/123/artifacts/out.png?X-Amz-Signature=abcdef1234567890&exp=300"
    scrubbed_url = scrub(sample_url)
    assert "abcdef1234567890" not in scrubbed_url
    assert "[redacted]" in scrubbed_url

    # 3. Secret keys in dictionary payloads
    payload = {
        "user_id": str(uuid4()),
        "authorization": "Bearer secret-token-xyz",
        "api_key": "provider-key-abc",
        "nested": {
            "password": "super-secret-password",
        },
    }
    scrubbed_dict = scrub(payload)
    assert scrubbed_dict["authorization"] == "[redacted]"
    assert scrubbed_dict["api_key"] == "[redacted]"
    assert scrubbed_dict["nested"]["password"] == "[redacted]"


def test_redact_filter_in_logging_pipeline() -> None:
    record = logging.LogRecord(
        name="fashx.tryon",
        level=logging.INFO,
        pathname="worker.py",
        lineno=42,
        msg="TryOn completed. Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.fakeSigXyz",
        args=(),
        exc_info=None,
    )
    redact_filter = RedactFilter()
    redact_filter.filter(record)
    assert "fakeSigXyz" not in record.msg
    assert "[redacted]" in record.msg
