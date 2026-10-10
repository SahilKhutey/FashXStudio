"""Unit tests for VLM enrichment schema, attribute extraction, try-on eligibility gating, and calibration."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from fashx.catalog.enrichment.schema import GarmentAttrs
from fashx.catalog.enrichment.vlm import MockVlmClient


def test_garment_attrs_schema() -> None:
    attrs = GarmentAttrs(
        category="top",
        sub_category="kurta",
        primary_color="blue",
        secondary_colors=["white"],
        pattern="printed",
        neckline="mandarin",
        sleeve_length="full",
        length="regular",
        fit="slim",
        ethnic_wear=True,
        ethnic_type="kurta",
        formality=3,
        occasions=["festive", "casual"],
        seasons=["summer"],
        photo_type="ghost_mannequin",
        tryon_suitable=True,
        tryon_reason="Clear frontal view",
        confidence={"category": 0.98, "sub_category": 0.95},
    )
    assert attrs.category == "top"
    assert attrs.ethnic_wear is True
    assert attrs.tryon_suitable is True

    # Invalid category enum
    with pytest.raises(PydanticValidationError):
        GarmentAttrs(
            category="invalid_category",  # type: ignore[arg-type]
            sub_category="item",
            primary_color="blue",
            pattern="solid",
            ethnic_wear=False,
            formality=3,
            photo_type="flat_lay",
            tryon_suitable=True,
            tryon_reason="ok",
        )

    # Formality out of bounds
    with pytest.raises(PydanticValidationError):
        GarmentAttrs(
            category="top",
            sub_category="shirt",
            primary_color="black",
            pattern="solid",
            ethnic_wear=False,
            formality=6,  # max is 5
            photo_type="on_model",
            tryon_suitable=True,
            tryon_reason="ok",
        )


def test_mock_vlm_client_extraction() -> None:
    client = MockVlmClient()

    # Ethnic kurta
    attrs = client.describe(
        b"dummy_jpeg",
        "Handblock Indigo Cotton Short Kurta",
        "Breathable traditional kurta with mandarin collar",
    )
    assert attrs.category == "top"
    assert attrs.sub_category == "kurta"
    assert attrs.ethnic_wear is True
    assert attrs.primary_color == "blue"
    assert attrs.pattern == "printed"
    assert attrs.tryon_suitable is True
    assert attrs.confidence["category"] >= 0.95

    # Complex saree (unsuitable for 2D VTO)
    saree_attrs = client.describe(
        b"dummy_jpeg",
        "Banarasi Katan Silk Saree with Zari Border",
        "Heavy bridal red saree",
    )
    assert saree_attrs.category == "one_piece"
    assert saree_attrs.sub_category == "saree"
    assert saree_attrs.ethnic_wear is True
    assert saree_attrs.tryon_suitable is False
    assert "drape" in saree_attrs.tryon_reason.lower()


def compute_tryon_eligibility(
    *,
    source_rights_tryon: bool,
    source_image_policy: str,
    vlm_tryon_suitable: bool,
    vlm_confidence: float,
    category: str,
    supported_categories: list[str],
    tau: float = 0.85,
) -> bool:
    """Evaluate 4-point try-on eligibility gate (Step 6.25)."""
    if not source_rights_tryon:
        return False
    if source_image_policy != "mirror":
        return False
    if not vlm_tryon_suitable:
        return False
    if vlm_confidence < tau:
        return False
    if category.lower() not in [c.lower() for c in supported_categories]:
        return False
    return True


def test_tryon_eligibility_multi_factor_gate() -> None:
    supported_cats = ["tops", "bottoms", "one-pieces", "top", "bottom", "one_piece"]

    # Baseline: all 4 conditions satisfied -> TRUE
    assert compute_tryon_eligibility(
        source_rights_tryon=True,
        source_image_policy="mirror",
        vlm_tryon_suitable=True,
        vlm_confidence=0.95,
        category="tops",
        supported_categories=supported_cats,
    ) is True

    # 1. Condition 1 fails: source rights_tryon is False
    assert compute_tryon_eligibility(
        source_rights_tryon=False,
        source_image_policy="mirror",
        vlm_tryon_suitable=True,
        vlm_confidence=0.95,
        category="tops",
        supported_categories=supported_cats,
    ) is False

    # 2. Condition 2 fails: image_policy is hotlink
    assert compute_tryon_eligibility(
        source_rights_tryon=True,
        source_image_policy="hotlink",
        vlm_tryon_suitable=True,
        vlm_confidence=0.95,
        category="tops",
        supported_categories=supported_cats,
    ) is False

    # 3. Condition 3 fails: tryon_suitable is False
    assert compute_tryon_eligibility(
        source_rights_tryon=True,
        source_image_policy="mirror",
        vlm_tryon_suitable=False,
        vlm_confidence=0.95,
        category="tops",
        supported_categories=supported_cats,
    ) is False

    # 3b. Condition 3 fails: confidence below tau (e.g. 0.70 < 0.85)
    assert compute_tryon_eligibility(
        source_rights_tryon=True,
        source_image_policy="mirror",
        vlm_tryon_suitable=True,
        vlm_confidence=0.70,
        category="tops",
        supported_categories=supported_cats,
        tau=0.85,
    ) is False

    # 4. Condition 4 fails: category unsupported (e.g. footwear / accessories)
    assert compute_tryon_eligibility(
        source_rights_tryon=True,
        source_image_policy="mirror",
        vlm_tryon_suitable=True,
        vlm_confidence=0.95,
        category="footwear",
        supported_categories=supported_cats,
    ) is False
