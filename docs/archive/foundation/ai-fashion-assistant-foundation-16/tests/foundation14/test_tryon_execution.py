from uuid import uuid4

import pytest

from api.app.tryon.domain.input_assembly import SUPPORTED_CATEGORIES, validate_garment_for_tryon
from api.app.tryon.integrations.gpu_client import ConfiguredTryOnProvider
from api.app.core.settings import Settings
from schemas.tryon.execution import TryOnExecutionInput


def test_only_supported_mvp_categories_are_accepted() -> None:
    validate_garment_for_tryon(category="dress", image_key="garments/a.jpg")
    for category in SUPPORTED_CATEGORIES:
        validate_garment_for_tryon(category=category, image_key="garments/a.jpg")


def test_unsupported_category_is_rejected() -> None:
    with pytest.raises(Exception) as exc:
        validate_garment_for_tryon(category="shoes", image_key="garments/a.jpg")
    assert "not supported" in str(exc.value)


def test_execution_contract_has_required_inputs() -> None:
    item = TryOnExecutionInput(
        job_id=uuid4(),
        user_id=uuid4(),
        photo_key="user-photos/u/p.jpg",
        garment_image_key="garments/g/m.jpg",
        model_version="v1",
        pipeline_version="foundation-14",
        artifact_key="abc",
        photo_version=1,
        garment_version=1,
    )
    assert item.photo_key.endswith(".jpg")


@pytest.mark.asyncio
async def test_provider_fails_closed_by_default(monkeypatch) -> None:
    monkeypatch.setattr("api.app.tryon.integrations.gpu_client.get_settings", lambda: Settings(TRYON_PROVIDER="disabled"))
    provider = ConfiguredTryOnProvider()
    with pytest.raises(Exception) as exc:
        await provider.submit(
            job_id=uuid4(),
            profile_photo_url="https://example/photo.jpg",
            garment_image_url="https://example/garment.jpg",
            model_version="v1",
            pipeline_version="p1",
        )
    assert getattr(exc.value, "code", "") == "gpu_provider_disabled"
