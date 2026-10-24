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
