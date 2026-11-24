"""Unit tests for GarmentImageValidator (Phase 07.3)."""

from __future__ import annotations

import io
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PIL import Image

from fashx.tryon.validation.contracts import Severity, ValidationStatus
from fashx.tryon.validation.error_codes import (
    GARMENT_BACKGROUND_UNSUITABLE,
    GARMENT_NOT_VISIBLE,
    GARMENT_PROCESSING_NOT_AUTHORIZED,
    IMAGE_PRODUCT_MISMATCH,
    PRODUCT_NOT_ACTIVE,
    UNSUPPORTED_GARMENT_CATEGORY,
)
from fashx.tryon.validation.garment_validator import GarmentImageValidator
from fashx.tryon.validation.visual_assessment import VisualAssessmentResponse


def make_valid_garment_bytes(size: tuple[int, int] = (800, 1000)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color="red").save(buf, format="JPEG")
    return buf.getvalue()


class FakeCatalogRepo:
    def __init__(self, product: object | None = None, image_associated: bool = True) -> None:
        self.product = product
        self.image_associated = image_associated

    async def get_by_id(self, product_id: object) -> object | None:
        return self.product

    async def get_product_image(self, product_id: object, image_asset_id: object) -> object | None:
        if self.image_associated:
            return SimpleNamespace(id=image_asset_id, storage_key="garments/img1.jpg")
        return None


class FakeAuthService:
    def __init__(self, authorized: bool = True) -> None:
        self.authorized = authorized

    async def has_permissions(self, source_id: object, required_permissions: list[str]) -> bool:
        return self.authorized


class FakeStorage:
    def __init__(self, data: bytes | None = None) -> None:
        self.data = data or make_valid_garment_bytes()

    def get(self, key: str) -> bytes | None:
        return self.data


class FakeVisualProvider:
    def __init__(self, response: VisualAssessmentResponse | None = None) -> None:
        self.response = response or VisualAssessmentResponse(
            garment_visible=True,
            crop_complete=True,
            background_suitable=True,
            confidence=0.92,
        )

    async def assess(self, request: object) -> VisualAssessmentResponse:
        return self.response


@pytest.mark.asyncio
async def test_garment_validator_happy_path() -> None:
    product_id = uuid4()
    image_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        status="ACTIVE",
        source_id=uuid4(),
        category="tops",
        image_storage_key="garments/img1.jpg",
    )
    validator = GarmentImageValidator(
        catalog_repository=FakeCatalogRepo(product=product, image_associated=True),
        authorization_service=FakeAuthService(authorized=True),
        storage=FakeStorage(),
        visual_provider=FakeVisualProvider(),
    )
    res = await validator.validate(
        product_id=product_id,
        image_asset_id=image_id,
        garment_category="tops",
    )
    assert res.status == ValidationStatus.PASSED
    assert res.can_proceed is True
    assert res.technical_metadata is not None
    assert res.visual_metadata is not None
    assert res.visual_metadata.garment_visible is True


@pytest.mark.asyncio
async def test_garment_validator_inactive_product_rejected() -> None:
    product_id = uuid4()
    image_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        status="DELISTED",  # Delisted
        source_id=uuid4(),
        category="tops",
    )
    validator = GarmentImageValidator(
        catalog_repository=FakeCatalogRepo(product=product),
        authorization_service=FakeAuthService(authorized=True),
        storage=FakeStorage(),
    )
    res = await validator.validate(
        product_id=product_id,
        image_asset_id=image_id,
        garment_category="tops",
    )
    assert res.status == ValidationStatus.REJECTED
    assert res.issues[0].code == PRODUCT_NOT_ACTIVE


@pytest.mark.asyncio
async def test_garment_validator_image_product_mismatch_rejected() -> None:
    product_id = uuid4()
    image_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        status="ACTIVE",
        source_id=uuid4(),
        category="tops",
    )
    # Image not associated with product
    validator = GarmentImageValidator(
        catalog_repository=FakeCatalogRepo(product=product, image_associated=False),
        authorization_service=FakeAuthService(authorized=True),
        storage=FakeStorage(),
    )
    res = await validator.validate(
        product_id=product_id,
        image_asset_id=image_id,
        garment_category="tops",
    )
    assert res.status == ValidationStatus.REJECTED
    assert res.issues[0].code == IMAGE_PRODUCT_MISMATCH


@pytest.mark.asyncio
async def test_garment_validator_missing_merchant_permission_rejected() -> None:
    product_id = uuid4()
    image_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        status="ACTIVE",
        source_id=uuid4(),
        category="tops",
        image_storage_key="garments/img.jpg",
    )
    validator = GarmentImageValidator(
        catalog_repository=FakeCatalogRepo(product=product, image_associated=True),
        authorization_service=FakeAuthService(authorized=False),  # Not authorized
        storage=FakeStorage(),
    )
    res = await validator.validate(
        product_id=product_id,
        image_asset_id=image_id,
        garment_category="tops",
    )
    assert res.status == ValidationStatus.REJECTED
    assert res.issues[0].code == GARMENT_PROCESSING_NOT_AUTHORIZED


@pytest.mark.asyncio
async def test_garment_validator_unsupported_category_rejected() -> None:
    product_id = uuid4()
    image_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        status="ACTIVE",
        source_id=uuid4(),
        category="jewellery",  # Unsupported
        image_storage_key="garments/ring.jpg",
    )
    validator = GarmentImageValidator(
        catalog_repository=FakeCatalogRepo(product=product, image_associated=True),
        authorization_service=FakeAuthService(authorized=True),
        storage=FakeStorage(),
    )
    res = await validator.validate(
        product_id=product_id,
        image_asset_id=image_id,
        garment_category="jewellery",
    )
    assert res.status == ValidationStatus.REJECTED
    assert res.issues[0].code == UNSUPPORTED_GARMENT_CATEGORY


@pytest.mark.asyncio
async def test_garment_validator_not_visible_rejected() -> None:
    product_id = uuid4()
    image_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        status="ACTIVE",
        source_id=uuid4(),
        category="tops",
        image_storage_key="garments/hidden.jpg",
    )
    not_visible_provider = FakeVisualProvider(
        VisualAssessmentResponse(garment_visible=False, confidence=0.85)
    )
    validator = GarmentImageValidator(
        catalog_repository=FakeCatalogRepo(product=product, image_associated=True),
        authorization_service=FakeAuthService(authorized=True),
        storage=FakeStorage(),
        visual_provider=not_visible_provider,
    )
    res = await validator.validate(
        product_id=product_id,
        image_asset_id=image_id,
        garment_category="tops",
    )
    assert res.status == ValidationStatus.REJECTED
    assert any(i.code == GARMENT_NOT_VISIBLE for i in res.issues)


@pytest.mark.asyncio
async def test_garment_validator_unsuitable_background_warning() -> None:
    product_id = uuid4()
    image_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        status="ACTIVE",
        source_id=uuid4(),
        category="tops",
        image_storage_key="garments/noisy.jpg",
    )
    noisy_bg_provider = FakeVisualProvider(
        VisualAssessmentResponse(
            garment_visible=True,
            crop_complete=True,
            background_suitable=False,
            confidence=0.88,
        )
    )
    validator = GarmentImageValidator(
        catalog_repository=FakeCatalogRepo(product=product, image_associated=True),
        authorization_service=FakeAuthService(authorized=True),
        storage=FakeStorage(),
        visual_provider=noisy_bg_provider,
    )
    res = await validator.validate(
        product_id=product_id,
        image_asset_id=image_id,
        garment_category="tops",
    )
    assert res.status == ValidationStatus.PASSED_WITH_WARNINGS
    assert res.can_proceed is True
    assert any(i.severity == Severity.WARNING for i in res.issues)
    assert any(i.code == GARMENT_BACKGROUND_UNSUITABLE for i in res.issues)
