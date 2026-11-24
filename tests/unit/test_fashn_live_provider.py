"""Unit and contract tests for Phase 07.2 FASHN live provider configuration and integration."""

from __future__ import annotations

import io
from uuid import uuid4

import httpx
import pytest
from PIL import Image

from fashx.application.ports.tryon import TryOnError, TryOnRequest
from fashx.core.release_config import ReleaseConfig, validate_release_config
from fashx.core.settings import Settings
from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter
from fashx.infrastructure.tryon.fashn_concurrency import FashnConcurrencyController
from fashx.infrastructure.tryon.fashn_errors import (
    map_fashn_http_error,
    map_fashn_status_error,
)
from fashx.infrastructure.tryon.fashn_health import (
    _sanitize_log_data,
    check_fashn_health,
)
from fashx.infrastructure.tryon.fashn_mapper import (
    build_fashn_run_payload,
    parse_fashn_status_response,
)
from fashx.tryon.ports import InferenceInput


def make_test_jpeg(size: tuple[int, int] = (512, 768), color: str = "blue") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format="JPEG")
    return buf.getvalue()


# ==============================================================================
# 1. Configuration & Safeguards Tests (P07-002-002 & P07-002-011)
# ==============================================================================


def test_fashn_settings_defaults_and_validation() -> None:
    s = Settings(
        TRYON_PROVIDER="mock",
        FASHN_BASE_URL="https://api.fashn.ai/v1",
        FASHN_CONNECT_TIMEOUT_SECONDS=5.0,
        FASHN_REQUEST_TIMEOUT_SECONDS=30.0,
        FASHN_READ_TIMEOUT_SECONDS=15.0,
        FASHN_SUBMIT_MAX_RETRIES=0,
        FASHN_STATUS_MAX_RETRIES=3,
        FASHN_POLL_INTERVAL_SECONDS=3.0,
        FASHN_PREDICTION_TIMEOUT_SECONDS=180,
        FASHN_MAX_CONCURRENT_PREDICTIONS=2,
        FASHN_MAX_SUBMISSIONS_PER_MINUTE=10,
    )
    assert s.fashn_base_url == "https://api.fashn.ai/v1"
    assert s.fashn_connect_timeout_seconds == 5.0
    assert s.fashn_request_timeout_seconds == 30.0
    assert s.fashn_status_max_retries == 3
    assert s.fashn_submit_max_retries == 0


def test_fashn_settings_fails_fast_on_missing_api_key_when_configured() -> None:
    with pytest.raises(ValueError, match="FASHN_API_KEY required"):
        Settings(
            TRYON_PROVIDER="fashn_api",
            FASHN_API_KEY="",
        )


def test_fashn_settings_rejects_insecure_http_base_url() -> None:
    with pytest.raises(ValueError, match="FASHN_BASE_URL must use HTTPS"):
        Settings(
            TRYON_PROVIDER="fashn_api",
            FASHN_API_KEY="test-key-123",
            FASHN_BASE_URL="http://insecure.fashn.ai/v1",
        )


def test_fashn_settings_rejects_negative_timeouts() -> None:
    with pytest.raises(ValueError, match="FASHN timeouts must be positive"):
        Settings(
            TRYON_PROVIDER="fashn_api",
            FASHN_API_KEY="test-key-123",
            FASHN_CONNECT_TIMEOUT_SECONDS=-1.0,
        )


def test_release_config_rejects_unimplemented_selfhost_in_staging_and_prod() -> None:
    # Staging rejecting fashn_selfhost
    cfg_staging = ReleaseConfig(
        app_env="staging",
        auth_mode="jwks",
        database_url="postgresql://user:pass@db.staging:5432/fashx",
        redis_url="redis://redis:6379/0",
        storage_backend="s3",
        tryon_provider="fashn_selfhost",
        cors_origins=["https://staging.fashx.com"],
        debug=False,
    )
    with pytest.raises(ValueError, match="fashn_selfhost is not implemented"):
        validate_release_config(cfg_staging)

    # Prod rejecting mock
    cfg_prod_mock = ReleaseConfig(
        app_env="production",
        auth_mode="jwks",
        database_url="postgresql://user:pass@db.prod:5432/fashx",
        redis_url="rediss://redis:6379/0",
        storage_backend="s3",
        tryon_provider="mock",
        cors_origins=["https://app.fashx.com"],
        debug=False,
    )
    with pytest.raises(ValueError, match="mock forbidden"):
        validate_release_config(cfg_prod_mock)


# ==============================================================================
# 2. Request and Response Mapper Tests (P07-002-003)
# ==============================================================================


def test_build_fashn_run_payload_v16_and_max() -> None:
    photo = make_test_jpeg(color="green")
    garment = make_test_jpeg(color="red")
    req = TryOnRequest(person_jpeg=photo, garment_jpeg=garment, category="tops")

    # v1.6 mapping
    payload_v16 = build_fashn_run_payload(req, model="tryon-v1.6", mode="balanced")
    assert payload_v16["model_name"] == "tryon-v1.6"
    assert payload_v16["inputs"]["category"] == "tops"
    assert payload_v16["inputs"]["mode"] == "balanced"
    assert payload_v16["inputs"]["model_image"].startswith("data:image/jpeg;base64,")
    assert payload_v16["inputs"]["garment_image"].startswith("data:image/jpeg;base64,")

    # Try-On Max mapping with custom options
    payload_max = build_fashn_run_payload(
        req,
        model="tryon-max",
        options={"nsfw_filter": True, "num_samples": 1},
    )
    assert payload_max["model_name"] == "tryon-max"
    assert payload_max["inputs"]["nsfw_filter"] is True
    assert payload_max["inputs"]["num_samples"] == 1


def test_parse_fashn_status_response_parsing() -> None:
    # 1. Successful completion with credits header
    completed_data = {
        "status": "completed",
        "output": ["https://cdn.fashn.ai/results/out1.jpg"],
    }
    headers = {"x-fashn-credits-used": "2.0"}
    res = parse_fashn_status_response(completed_data, headers=headers)
    assert res.is_success is True
    assert res.is_terminal is True
    assert res.output_urls == ["https://cdn.fashn.ai/results/out1.jpg"]
    assert res.credits_used == 2.0

    # 2. In-queue / processing pending status
    pending_data = {"status": "processing"}
    res_pending = parse_fashn_status_response(pending_data)
    assert res_pending.is_success is False
    assert res_pending.is_terminal is False

    # 3. Failed status with error object
    failed_data = {
        "status": "failed",
        "error": {"name": "PoseError", "message": "No person detected"},
    }
    res_failed = parse_fashn_status_response(failed_data)
    assert res_failed.is_success is False
    assert res_failed.is_terminal is True
    assert res_failed.error_name == "PoseError"
    assert "No person detected" in (res_failed.error_message or "")


# ==============================================================================
# 3. Error Mapping Tests (P07-002-004 & P07-002-005)
# ==============================================================================


def test_map_fashn_http_error_codes() -> None:
    # 400 Bad Request
    err_400 = map_fashn_http_error(400, "Invalid JSON input")
    assert err_400.code == "bad_input"
    assert err_400.retryable is False

    # 401 Unauthorized
    err_401 = map_fashn_http_error(401, "Unauthorized")
    assert err_401.code == "provider_auth"
    assert err_401.retryable is False

    # 402 Payment Required
    err_402 = map_fashn_http_error(402, "Credits exhausted")
    assert err_402.code == "provider_credits"
    assert err_402.retryable is False

    # 429 Rate Limit
    err_429 = map_fashn_http_error(429, "Too Many Requests")
    assert err_429.code == "provider_unavailable"
    assert err_429.retryable is True

    # 503 Service Unavailable
    err_503 = map_fashn_http_error(503, "Temporary Gateway Error")
    assert err_503.code == "provider_unavailable"
    assert err_503.retryable is True


def test_map_fashn_status_errors() -> None:
    # Pose error -> user error
    err_pose = map_fashn_status_error("PoseError", "No human pose found in image")
    assert err_pose.code == "bad_input"
    assert err_pose.retryable is False
    assert "person" in err_pose.user_message

    # Safety policy violation
    err_nsfw = map_fashn_status_error("ContentPolicyViolation", "NSFW content detected")
    assert err_nsfw.code == "policy_violation"
    assert err_nsfw.retryable is False

    # Pipeline infrastructure error -> retryable
    err_pipe = map_fashn_status_error("PipelineError", "GPU worker terminated unexpectedly")
    assert err_pipe.code == "provider_unavailable"
    assert err_pipe.retryable is True


# ==============================================================================
# 4. Health Check & Structured Logging Tests (P07-002-007)
# ==============================================================================


def test_check_fashn_health_probes() -> None:
    # Healthy with credits
    client_healthy = httpx.Client(
        base_url="https://api.fashn.ai/v1",
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"credits": 150.0})),
    )
    rep_healthy = check_fashn_health(client_healthy)
    assert rep_healthy.status == "HEALTHY"
    assert rep_healthy.healthy is True
    assert rep_healthy.credits_remaining == 150.0

    # Degraded (0 credits)
    client_degraded = httpx.Client(
        base_url="https://api.fashn.ai/v1",
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"credits": 0.0})),
    )
    rep_degraded = check_fashn_health(client_degraded)
    assert rep_degraded.status == "DEGRADED"
    assert rep_degraded.healthy is False

    # Unhealthy (401 auth rejected)
    client_unhealthy = httpx.Client(
        base_url="https://api.fashn.ai/v1",
        transport=httpx.MockTransport(lambda req: httpx.Response(401, text="Unauthorized")),
    )
    rep_unhealthy = check_fashn_health(client_unhealthy)
    assert rep_unhealthy.status == "UNHEALTHY"
    assert rep_unhealthy.healthy is False


def test_sanitize_log_data_scrubs_secrets_and_binary() -> None:
    data = {
        "api_key": "live_fashn_secret_token_12345",
        "authorization": "Bearer token",
        "person_image": b"\xff\xd8\xff" + b"0" * 500,
        "garment_b64": "data:image/jpeg;base64," + "A" * 600,
        "provider_job_id": "job-abc-123",
        "status": "completed",
    }
    sanitized = _sanitize_log_data(data)
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["person_image"] == "<503 bytes>"
    assert "chars" in sanitized["garment_b64"]
    assert sanitized["provider_job_id"] == "job-abc-123"
    assert sanitized["status"] == "completed"


# ==============================================================================
# 5. Concurrency & Rate Limiting Tests (P07-002-009)
# ==============================================================================


def test_fashn_concurrency_controller() -> None:
    ctrl = FashnConcurrencyController(max_concurrent=2, max_submissions_per_minute=2)

    # 1. Submissions rate limiter
    ctrl.acquire_submission_slot()
    ctrl.acquire_submission_slot()
    with pytest.raises(TryOnError, match="Rate limit exceeded"):
        ctrl.acquire_submission_slot()

    # 2. Concurrency slots
    ctrl.acquire_prediction_slot()
    ctrl.acquire_prediction_slot()
    assert ctrl.active_count == 2
    with pytest.raises(TryOnError, match="Concurrency cap reached"):
        ctrl.acquire_prediction_slot()

    ctrl.release_prediction_slot()
    assert ctrl.active_count == 1
    ctrl.acquire_prediction_slot()
    assert ctrl.active_count == 2


# ==============================================================================
# 6. Adapter Submit, Collect & Download Contract (P07-002-006 & P07-002-008)
# ==============================================================================


def test_fashn_api_full_lifecycle_and_cost_accounting() -> None:
    test_jpeg = make_test_jpeg()
    poll_count = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal poll_count
        if request.method == "POST" and request.url.path == "/v1/run":
            assert "Authorization" in request.headers
            return httpx.Response(200, json={"id": "fashn-job-lifecycle-1"})
        if request.method == "GET" and request.url.path == "/v1/status/fashn-job-lifecycle-1":
            poll_count += 1
            if poll_count == 1:
                return httpx.Response(200, json={"status": "in_queue"})
            return httpx.Response(
                200,
                headers={"x-fashn-credits-used": "1.0"},
                json={
                    "status": "completed",
                    "output": ["https://cdn.fashn.ai/results/out123.jpg"],
                },
            )
        return httpx.Response(404)

    def mock_dl_handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://cdn.fashn.ai/results/out123.jpg"
        assert "Authorization" not in request.headers  # Dedicated client must NOT send auth
        return httpx.Response(200, content=test_jpeg)

    client = httpx.Client(
        base_url="https://api.fashn.ai/v1",
        transport=httpx.MockTransport(mock_handler),
    )
    dl_client = httpx.Client(transport=httpx.MockTransport(mock_dl_handler))

    adapter = FashnApiAdapter(
        api_key="secret-key",
        client=client,
        download_client=dl_client,
        cost_per_credit_usd=0.075,
        sleep=lambda _: None,
    )

    req = TryOnRequest(person_jpeg=test_jpeg, garment_jpeg=test_jpeg, category="tops")
    out = adapter.run(req)

    assert out.provider == "fashn_api"
    assert out.provider_job_id == "fashn-job-lifecycle-1"
    assert out.cost_usd_est == 0.075
    assert out.credits_used == 1.0
    assert poll_count == 2
    assert out.image_bytes is not None


def test_fashn_api_polling_retries_transient_transport_error() -> None:
    test_jpeg = make_test_jpeg()
    attempt = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt
        if request.method == "POST" and request.url.path == "/v1/run":
            return httpx.Response(200, json={"id": "job-retry-net"})
        if request.method == "GET" and request.url.path == "/v1/status/job-retry-net":
            attempt += 1
            if attempt == 1:
                # First attempt raises transport error
                raise httpx.ConnectError("Connection reset by peer")
            # Second attempt succeeds
            return httpx.Response(
                200,
                json={
                    "status": "completed",
                    "output": ["https://cdn.fashn.ai/results/retry.jpg"],
                },
            )
        return httpx.Response(404)

    client = httpx.Client(
        base_url="https://api.fashn.ai/v1",
        transport=httpx.MockTransport(mock_handler),
    )
    dl_client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, content=test_jpeg))
    )

    adapter = FashnApiAdapter(
        api_key="secret-key",
        client=client,
        download_client=dl_client,
        status_max_retries=2,
        sleep=lambda _: None,
    )

    out = adapter.run(TryOnRequest(person_jpeg=test_jpeg, garment_jpeg=test_jpeg))
    assert out.provider_job_id == "job-retry-net"
    assert attempt == 2


@pytest.mark.asyncio
async def test_fashn_adapter_execute_tryon_populates_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    from fashx.application.ports.tryon import TryOnOutput

    adapter = FashnApiAdapter(api_key="test-key")
    fake_output = TryOnOutput(
        image_bytes=make_test_jpeg(),
        provider="fashn_api",
        model="tryon-v1.6",
        provider_job_id="fashn-job-async",
        latency_ms=150,
        cost_usd_est=0.075,
        credits_used=1.0,
    )

    async def fake_to_thread(func, *args, **kwargs):
        return fake_output

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    payload = InferenceInput(
        job_id=uuid4(),
        user_id=uuid4(),
        garment_id=uuid4(),
        user_photo_bytes=make_test_jpeg(),
        garment_image_bytes=make_test_jpeg(),
        garment_category="tops",
    )
    out = await adapter.execute_tryon(payload)
    assert out.rendered_image_bytes is not None
    assert out.raw_metadata["provider"] == "fashn_api"
    assert out.raw_metadata["provider_job_id"] == "fashn-job-async"
    assert out.raw_metadata["cost_usd_est"] == 0.075
    assert out.raw_metadata["credits_used"] == 1.0
