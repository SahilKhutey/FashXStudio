from uuid import uuid4

from schemas.catalog.garment import CanonicalGarment, MerchantOffer
from schemas.common.enums import BuildType, FitVerdict, TryOnStatus
from schemas.feedback.fit import FitFeedbackCreate
from schemas.identity.user import UserCreate
from schemas.profile.body import BodyProfile
from schemas.tryon.job import TryOnCreate


def test_profile_contract_validates_ranges() -> None:
    profile = UserCreate(height_cm=170, weight_kg=66)
    assert profile.height_cm == 170
    assert profile.weight_kg == 66


def test_body_profile_uses_typed_build() -> None:
    profile = BodyProfile(height_cm=170, weight_kg=66, build=BuildType.ATHLETIC)
    assert profile.build is BuildType.ATHLETIC


def test_tryon_contract_is_user_agnostic() -> None:
    garment_id = uuid4()
    request = TryOnCreate(product_id=garment_id)
    assert request.product_id == garment_id


def test_catalog_contracts_separate_garment_and_offer() -> None:
    garment = CanonicalGarment(id=uuid4(), category="dress")
    offer = MerchantOffer(
        id=uuid4(),
        garment_id=garment.id,
        merchant_id=uuid4(),
        source_product_id="sku-1",
        url="https://merchant.example/p/1",
        price_minor=129900,
    )
    assert offer.garment_id == garment.id
    assert offer.currency == "INR"


def test_fit_feedback_keeps_physical_fit_distinct() -> None:
    feedback = FitFeedbackCreate(
        garment_id=uuid4(),
        brand_id=uuid4(),
        category="shirt",
        fit_type="regular",
        size_label="M",
        verdict=FitVerdict.TRUE_TO_SIZE,
    )
    assert feedback.verdict is FitVerdict.TRUE_TO_SIZE


def test_tryon_status_enum_contains_async_terminal_states() -> None:
    assert TryOnStatus.QUEUED.value == "queued"
    assert TryOnStatus.COMPLETED.value == "completed"
    assert TryOnStatus.FAILED.value == "failed"
