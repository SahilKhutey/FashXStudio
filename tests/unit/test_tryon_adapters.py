from uuid import uuid4

import pytest

from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter
from fashx.ml.licenses import ALLOWED_LICENSE_IDS, assert_production_license
from fashx.tryon.adapters.mock_adapter import MockAdapter, MockTryOnAdapter
from fashx.tryon.ports import InferenceInput


@pytest.mark.asyncio
async def test_mock_tryon_adapter_execution() -> None:
    adapter = MockTryOnAdapter()
    assert adapter.is_commercial_cleared is False
    assert adapter.provider == "mock"
    assert adapter.model_version == "mock-vto-v1"

    payload = InferenceInput(
        job_id=uuid4(),
        user_id=uuid4(),
        garment_id=uuid4(),
        user_photo_bytes=b"dummy_user_photo",
        garment_image_bytes=b"dummy_garment_photo",
        garment_category="tops",
    )
    output = await adapter.execute_tryon(payload)
    assert output.rendered_image_bytes is not None
    assert output.model_version == "mock-vto-v1"
    assert output.inference_latency_ms >= 0.0


def test_fashn_api_adapter_license_guard() -> None:
    # 1. Real commercial adapter declares commercial-api license
    adapter = FashnApiAdapter(api_key="test-key")
    assert adapter.license_id == "commercial-api"
    assert adapter.license_id in ALLOWED_LICENSE_IDS
    assert_production_license(adapter)  # must not raise

    # 2. Mock adapter must be rejected by production license guard (Rule I08)
    mock = MockAdapter()
    assert mock.license_id == "mock"
    with pytest.raises(RuntimeError, match="not allowed in production"):
        assert_production_license(mock)

    # 3. Arbitrary / unknown license must be rejected
    class UnlicensedAdapter:
        license_id = "research-only"

    with pytest.raises(RuntimeError, match="not allowed in production"):
        assert_production_license(UnlicensedAdapter())


@pytest.mark.asyncio
async def test_fashn_api_adapter_conforms_to_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = FashnApiAdapter(api_key="test-key", model="tryon-v1.6")
    assert adapter.is_commercial_cleared is True
    assert adapter.provider == "fashn_api"
    assert adapter.model_version == "tryon-v1.6"
    assert adapter.pipeline_version == "fashn-hosted-v1"

    # Mock run method to verify execute_tryon delegation
    from fashx.application.ports.tryon import TryOnOutput

    fake_output = TryOnOutput(
        image_bytes=b"dummy_result",
        provider="fashn_api",
        model="tryon-v1.6",
        provider_job_id="fashn-job-123",
        latency_ms=120,
        cost_usd_est=0.075,
    )
    monkeypatch.setattr(adapter, "run", lambda req, deadline_s=90.0: fake_output)

    payload = InferenceInput(
        job_id=uuid4(),
        user_id=uuid4(),
        garment_id=uuid4(),
        user_photo_bytes=b"user_bytes",
        garment_image_bytes=b"garment_bytes",
        garment_category="tops",
    )
    res = await adapter.execute_tryon(payload)
    assert res.rendered_image_bytes == b"dummy_result"
    assert res.model_version == "tryon-v1.6"
    assert res.pipeline_version == "fashn-hosted-v1"
    assert res.raw_metadata["provider"] == "fashn_api"
    assert res.raw_metadata["provider_job_id"] == "fashn-job-123"


def test_get_tryon_adapter_fail_closed_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from fashx.core.dependencies import get_tryon_adapter
    from fashx.core.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("TRYON_PROVIDER", "fashn_api")
    monkeypatch.delenv("FASHN_API_KEY", raising=False)

    with pytest.raises(ValueError, match="FASHN_API_KEY required"):
        get_tryon_adapter()
    get_settings.cache_clear()


def make_test_jpeg() -> bytes:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="blue").save(buf, format="JPEG")
    return buf.getvalue()


def test_fashn_api_submit_collect_mock_transport() -> None:
    """Test full submit, polling, and CDN download lifecycle on FashnApiAdapter."""
    import httpx

    from fashx.application.ports.tryon import TryOnRequest

    test_jpeg = make_test_jpeg()
    poll_count = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal poll_count
        if request.method == "POST" and request.url.path == "/v1/run":
            assert "Authorization" in request.headers
            return httpx.Response(200, json={"id": "fashn-job-xyz"})
        if request.method == "GET" and request.url.path == "/v1/status/fashn-job-xyz":
            poll_count += 1
            if poll_count == 1:
                return httpx.Response(200, json={"status": "in_queue"})
            return httpx.Response(
                200,
                json={
                    "status": "completed",
                    "output": ["https://cdn.fashn.ai/results/job-xyz.jpg"],
                },
            )
        return httpx.Response(404)

    def mock_dl_handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://cdn.fashn.ai/results/job-xyz.jpg"
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
        sleep=lambda _: None,
    )

    req = TryOnRequest(person_jpeg=test_jpeg, garment_jpeg=test_jpeg, category="tops")
    out = adapter.run(req)

    assert out.provider == "fashn_api"
    assert out.provider_job_id == "fashn-job-xyz"
    assert out.image_bytes is not None
    assert poll_count == 2


def test_fashn_api_error_mappings_and_ssrf_guard() -> None:
    """Test HTTP status code error mapping and SSRF protection on CDN download."""
    import httpx

    from fashx.application.ports.tryon import TryOnError, TryOnRequest

    test_jpeg = make_test_jpeg()

    # 1. 401 Unauthorized -> provider_auth
    client_401 = httpx.Client(
        base_url="https://api.fashn.ai/v1",
        transport=httpx.MockTransport(lambda req: httpx.Response(401, text="Unauthorized")),
    )
    adapter_401 = FashnApiAdapter(api_key="bad-key", client=client_401, sleep=lambda _: None)
    with pytest.raises(TryOnError) as exc_401:
        adapter_401.submit(TryOnRequest(person_jpeg=test_jpeg, garment_jpeg=test_jpeg))
    assert exc_401.value.code == "provider_auth"
    assert exc_401.value.retryable is False

    # 2. 429 Rate Limit -> provider_unavailable
    client_429 = httpx.Client(
        base_url="https://api.fashn.ai/v1",
        transport=httpx.MockTransport(lambda req: httpx.Response(429, text="Rate limit")),
    )
    adapter_429 = FashnApiAdapter(api_key="key", client=client_429, sleep=lambda _: None)
    with pytest.raises(TryOnError) as exc_429:
        adapter_429.submit(TryOnRequest(person_jpeg=test_jpeg, garment_jpeg=test_jpeg))
    assert exc_429.value.code == "provider_unavailable"
    assert exc_429.value.retryable is True

    # 3. SSRF Protection: rejecting download from non-fashn host
    def mock_status_ssrf(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/run":
            return httpx.Response(200, json={"id": "job-ssrf"})
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": ["https://evil-attacker.example.com/exploit.jpg"],
            },
        )

    client_ssrf = httpx.Client(
        base_url="https://api.fashn.ai/v1",
        transport=httpx.MockTransport(mock_status_ssrf),
    )
    adapter_ssrf = FashnApiAdapter(api_key="key", client=client_ssrf, sleep=lambda _: None)
    with pytest.raises(TryOnError) as exc_ssrf:
        adapter_ssrf.run(TryOnRequest(person_jpeg=test_jpeg, garment_jpeg=test_jpeg))
    assert exc_ssrf.value.code == "provider_bad_url"


def test_process_job_use_case_dynamic_adapter_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify ProcessTryOnJobUseCase dynamically resolves configured try-on provider."""
    from fashx.core.settings import get_settings
    from fashx.tryon.application.process_job import ProcessTryOnJobUseCase

    get_settings.cache_clear()
    monkeypatch.setenv("TRYON_PROVIDER", "fashn_api")
    monkeypatch.setenv("FASHN_API_KEY", "fashn_live_secret")

    uc = ProcessTryOnJobUseCase(
        tryon_uow=None,  # type: ignore[arg-type]
        profile_uow=None,  # type: ignore[arg-type]
        catalog_uow=None,  # type: ignore[arg-type]
        adapter=None,
    )
    assert isinstance(uc.adapter, FashnApiAdapter)
    assert uc.adapter.provider == "fashn_api"

    get_settings.cache_clear()
