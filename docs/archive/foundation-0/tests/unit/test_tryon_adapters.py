from uuid import uuid4

import pytest
from api.app.tryon.adapters.commercial_api_adapter import CommercialApiAdapter
from api.app.tryon.adapters.mock_adapter import MockTryOnAdapter
from api.app.tryon.adapters.research_diffusion_adapter import (
    CommercialLicenseViolationError,
    ResearchDiffusionAdapter,
)
from api.app.tryon.ports import InferenceInput


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


@pytest.mark.asyncio
async def test_commercial_api_adapter_execution() -> None:
    adapter = CommercialApiAdapter()
    assert adapter.is_commercial_cleared is True

    payload = InferenceInput(
        job_id=uuid4(),
        user_id=uuid4(),
        garment_id=uuid4(),
        user_photo_bytes=b"user_bytes",
        garment_image_bytes=b"garment_bytes",
        garment_category="tops",
    )
    output = await adapter.execute_tryon(payload)
    assert output.raw_metadata.get("provider") == "commercial_licensed_api"


@pytest.mark.asyncio
async def test_research_diffusion_adapter_license_guard() -> None:
    # 1. Evaluation mode is allowed
    eval_adapter = ResearchDiffusionAdapter(environment="test", allow_research_mode=True)
    assert eval_adapter.is_commercial_cleared is False

    payload = InferenceInput(
        job_id=uuid4(),
        user_id=uuid4(),
        garment_id=uuid4(),
        user_photo_bytes=b"user_bytes",
        garment_image_bytes=b"garment_bytes",
        garment_category="dresses",
    )
    res = await eval_adapter.execute_tryon(payload)
    assert res.raw_metadata.get("license") == "Non-Commercial / Academic Research Only"

    # 2. Production mode without research flag must fail (Rule I08)
    prod_adapter = ResearchDiffusionAdapter(environment="production", allow_research_mode=False)
    with pytest.raises(CommercialLicenseViolationError) as exc_info:
        await prod_adapter.execute_tryon(payload)

    assert "academic non-commercial license" in str(exc_info.value)
