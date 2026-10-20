from uuid import uuid4

import pytest

from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter
from fashx.ml.licenses import ALLOWED_LICENSE_IDS, assert_production_license
from fashx.tryon.adapters.mock_adapter import MockAdapter, MockTryOnAdapter
from fashx.tryon.ports import InferenceInput


@pytest.mark.asyncio
async def test_mock_tryon_adapter_execution() -> None:
    adapter = MockTryOnAdapter()
    assert adapter.is_commercial_cleared is True
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
