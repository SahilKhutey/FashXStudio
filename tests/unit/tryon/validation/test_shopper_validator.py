"""Unit tests for ShopperImageValidator (Phase 07.3)."""

from __future__ import annotations

import io
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PIL import Image

from fashx.tryon.validation.contracts import Severity, ValidationStatus
from fashx.tryon.validation.error_codes import (
    BODY_REGION_NOT_VISIBLE,
    BODY_REGION_OCCLUDED,
    IMAGE_NOT_ACTIVE,
    IMAGE_NOT_OWNED_OR_NOT_FOUND,
    MULTIPLE_PEOPLE_DETECTED,
    PERSON_NOT_DETECTED,
    UNSUPPORTED_GARMENT_CATEGORY,
    VTO_CONSENT_REQUIRED,
)
from fashx.tryon.validation.shopper_validator import ShopperImageValidator
from fashx.tryon.validation.visual_assessment import VisualAssessmentResponse


def make_valid_photo_bytes(size: tuple[int, int] = (768, 1024)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color="blue").save(buf, format="JPEG")
    return buf.getvalue()


class FakeConsentRepo:
    def __init__(self, has_consent: bool = True) -> None:
        self._has_consent = has_consent

    async def has_active_consent(self, user_id: object, purpose: str) -> bool:
        return self._has_consent


class FakeAssetRepo:
    def __init__(self, photo: object | None = None) -> None:
        self.photo = photo

    async def get_by_id(self, photo_id: object) -> object | None:
        return self.photo


class FakeStorage:
    def __init__(self, data: bytes | None = None) -> None:
        self.data = data or make_valid_photo_bytes()

    def get(self, key: str) -> bytes | None:
        return self.data


class FakeVisualProvider:
    def __init__(self, response: VisualAssessmentResponse | None = None) -> None:
        self.response = response or VisualAssessmentResponse(
            person_detected=True,
            person_count=1,
            visible_regions=["shoulders", "torso", "waist", "legs"],
            pose_label="UPRIGHT_FRONT",
            confidence=0.92,
        )

    async def assess(self, request: object) -> VisualAssessmentResponse:
        return self.response


@pytest.mark.asyncio
async def test_shopper_validator_happy_path() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    photo = SimpleNamespace(
        id=photo_id,
        user_id=user_id,
        status="accepted",
        storage_key="photos/valid.jpg",
        version=2,
    )
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=True),
        asset_repository=FakeAssetRepo(photo=photo),
        storage=FakeStorage(),
        visual_provider=FakeVisualProvider(),
    )
    res = await validator.validate(
        user_id=user_id, asset_id=photo_id, garment_category="tops"
    )
    assert res.status == ValidationStatus.PASSED
    assert res.can_proceed is True
    assert res.asset_version == "2"
    assert res.technical_metadata is not None
    assert res.visual_metadata is not None
    assert res.visual_metadata.person_detected is True


@pytest.mark.asyncio
async def test_shopper_validator_missing_consent_rejected() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=False),
        asset_repository=FakeAssetRepo(),
        storage=FakeStorage(),
    )
    res = await validator.validate(
        user_id=user_id, asset_id=photo_id, garment_category="tops"
    )
    assert res.status == ValidationStatus.REJECTED
    assert res.can_proceed is False
    assert res.issues[0].code == VTO_CONSENT_REQUIRED


@pytest.mark.asyncio
async def test_shopper_validator_cross_user_asset_rejected() -> None:
    owner_id = uuid4()
    attacker_id = uuid4()
    photo_id = uuid4()
    photo = SimpleNamespace(
        id=photo_id,
        user_id=owner_id,  # Owned by different user
        status="accepted",
        storage_key="photos/private.jpg",
        version=1,
    )
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=True),
        asset_repository=FakeAssetRepo(photo=photo),
        storage=FakeStorage(),
    )
    # Attacker tries to access owner's photo
    res = await validator.validate(
        user_id=attacker_id, asset_id=photo_id, garment_category="tops"
    )
    assert res.status == ValidationStatus.REJECTED
    assert res.can_proceed is False
    assert res.issues[0].code == IMAGE_NOT_OWNED_OR_NOT_FOUND


@pytest.mark.asyncio
async def test_shopper_validator_inactive_asset_rejected() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    photo = SimpleNamespace(
        id=photo_id,
        user_id=user_id,
        status="rejected",  # Inactive
        storage_key="photos/bad.jpg",
        version=1,
    )
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=True),
        asset_repository=FakeAssetRepo(photo=photo),
        storage=FakeStorage(),
    )
    res = await validator.validate(
        user_id=user_id, asset_id=photo_id, garment_category="tops"
    )
    assert res.status == ValidationStatus.REJECTED
    assert res.issues[0].code == IMAGE_NOT_ACTIVE


@pytest.mark.asyncio
async def test_shopper_validator_person_missing_rejected() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    photo = SimpleNamespace(
        id=photo_id,
        user_id=user_id,
        status="accepted",
        storage_key="photos/landscape.jpg",
        version=1,
    )
    no_person_provider = FakeVisualProvider(
        VisualAssessmentResponse(person_detected=False, confidence=0.90)
    )
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=True),
        asset_repository=FakeAssetRepo(photo=photo),
        storage=FakeStorage(),
        visual_provider=no_person_provider,
    )
    res = await validator.validate(
        user_id=user_id, asset_id=photo_id, garment_category="tops"
    )
    assert res.status == ValidationStatus.REJECTED
    assert any(i.code == PERSON_NOT_DETECTED for i in res.issues)


@pytest.mark.asyncio
async def test_shopper_validator_multiple_people_rejected() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    photo = SimpleNamespace(
        id=photo_id,
        user_id=user_id,
        status="accepted",
        storage_key="photos/group.jpg",
        version=1,
    )
    multi_person_provider = FakeVisualProvider(
        VisualAssessmentResponse(person_detected=True, person_count=3, confidence=0.85)
    )
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=True),
        asset_repository=FakeAssetRepo(photo=photo),
        storage=FakeStorage(),
        visual_provider=multi_person_provider,
    )
    res = await validator.validate(
        user_id=user_id, asset_id=photo_id, garment_category="tops"
    )
    assert res.status == ValidationStatus.REJECTED
    assert any(i.code == MULTIPLE_PEOPLE_DETECTED for i in res.issues)


@pytest.mark.asyncio
async def test_shopper_validator_missing_required_regions_rejected() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    photo = SimpleNamespace(
        id=photo_id,
        user_id=user_id,
        status="accepted",
        storage_key="photos/headshot.jpg",
        version=1,
    )
    # Headshot only has shoulders, missing torso
    headshot_provider = FakeVisualProvider(
        VisualAssessmentResponse(
            person_detected=True,
            person_count=1,
            visible_regions=["head", "shoulders"],
            confidence=0.88,
        )
    )
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=True),
        asset_repository=FakeAssetRepo(photo=photo),
        storage=FakeStorage(),
        visual_provider=headshot_provider,
    )
    # Tops require shoulders and torso
    res = await validator.validate(
        user_id=user_id, asset_id=photo_id, garment_category="tops"
    )
    assert res.status == ValidationStatus.REJECTED
    assert any(i.code == BODY_REGION_NOT_VISIBLE for i in res.issues)


@pytest.mark.asyncio
async def test_shopper_validator_severe_occlusion_rejected() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    photo = SimpleNamespace(
        id=photo_id,
        user_id=user_id,
        status="accepted",
        storage_key="photos/blocked.jpg",
        version=1,
    )
    occluded_provider = FakeVisualProvider(
        VisualAssessmentResponse(
            person_detected=True,
            person_count=1,
            visible_regions=["shoulders", "torso"],
            occlusion_detected=True,
            occlusion_severity="SEVERE",
            confidence=0.85,
        )
    )
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=True),
        asset_repository=FakeAssetRepo(photo=photo),
        storage=FakeStorage(),
        visual_provider=occluded_provider,
    )
    res = await validator.validate(
        user_id=user_id, asset_id=photo_id, garment_category="tops"
    )
    assert res.status == ValidationStatus.REJECTED
    assert any(i.code == BODY_REGION_OCCLUDED for i in res.issues)


@pytest.mark.asyncio
async def test_shopper_validator_minor_occlusion_warning() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    photo = SimpleNamespace(
        id=photo_id,
        user_id=user_id,
        status="accepted",
        storage_key="photos/minor_occlusion.jpg",
        version=1,
    )
    minor_occluded_provider = FakeVisualProvider(
        VisualAssessmentResponse(
            person_detected=True,
            person_count=1,
            visible_regions=["shoulders", "torso"],
            occlusion_detected=True,
            occlusion_severity="MINOR",
            confidence=0.88,
        )
    )
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=True),
        asset_repository=FakeAssetRepo(photo=photo),
        storage=FakeStorage(),
        visual_provider=minor_occluded_provider,
    )
    res = await validator.validate(
        user_id=user_id, asset_id=photo_id, garment_category="tops"
    )
    assert res.status == ValidationStatus.PASSED_WITH_WARNINGS
    assert res.can_proceed is True
    assert any(i.severity == Severity.WARNING for i in res.issues)


@pytest.mark.asyncio
async def test_shopper_validator_unsupported_category_rejected() -> None:
    user_id = uuid4()
    photo_id = uuid4()
    photo = SimpleNamespace(
        id=photo_id,
        user_id=user_id,
        status="accepted",
        storage_key="photos/valid.jpg",
        version=1,
    )
    validator = ShopperImageValidator(
        consent_repository=FakeConsentRepo(has_consent=True),
        asset_repository=FakeAssetRepo(photo=photo),
        storage=FakeStorage(),
    )
    res = await validator.validate(
        user_id=user_id, asset_id=photo_id, garment_category="footwear"
    )
    assert res.status == ValidationStatus.REJECTED
    assert any(i.code == UNSUPPORTED_GARMENT_CATEGORY for i in res.issues)
