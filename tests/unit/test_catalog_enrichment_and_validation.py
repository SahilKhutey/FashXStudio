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


@pytest.mark.parametrize(
    "case_name, source_policy, source_rights, enrichment_suitable, enrichment_conf, category, expected",
    [
        ("hotlink source gives false", "hotlink", True, True, 0.95, "tops", False),
        ("no try-on rights gives false", "mirror", False, True, 0.95, "tops", False),
        ("unsuitable enrichment gives false", "mirror", True, False, 0.95, "tops", False),
        ("unsupported category gives false", "mirror", True, True, 0.95, "footwear", False),
        ("all four satisfied gives true", "mirror", True, True, 0.95, "tops", True),
    ],
)
def test_backfill_cases_table(
    case_name: str,
    source_policy: str,
    source_rights: bool,
    enrichment_suitable: bool,
    enrichment_conf: float,
    category: str,
    expected: bool,
) -> None:
    from scripts.catalog.backfill_tryon_supported import evaluate_garment_tryon_eligibility

    res = evaluate_garment_tryon_eligibility(
        category=category,
        source_rights_tryon=source_rights,
        source_image_policy=source_policy,
        source_status="cleared",
        vlm_tryon_suitable=enrichment_suitable,
        vlm_confidence=enrichment_conf,
    )
    assert res == expected, f"Failed case '{case_name}': expected {expected}, got {res}"


def test_backfill_cli_argparse_defaults_to_dry_run() -> None:
    from scripts.catalog.backfill_tryon_supported import parse_args

    assert parse_args([]).dry_run is True
    assert parse_args(["--dry-run"]).dry_run is True
    assert parse_args(["--apply"]).dry_run is False


@pytest.mark.asyncio
async def test_backfill_tryon_supported_unit() -> None:
    """Unit test for backfill_tryon_supported verifying dry-run default, enrichment, and apply behavior."""
    from uuid import uuid4

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    from database.models import Base
    from database.models.catalog import (
        CanonicalGarment,
        CatalogSource,
        GarmentEnrichment,
        Merchant,
        MerchantOffer,
        MerchantProduct,
    )
    from scripts.catalog.backfill_tryon_supported import backfill_tryon_supported

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        # 1. Sources: s1 is cleared + mirror + rights_tryon; s2 is pending + hotlink
        s1 = CatalogSource(
            id=uuid4(),
            slug="brand-cleared",
            name="Brand Cleared",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        s2 = CatalogSource(
            id=uuid4(),
            slug="brand-pending",
            name="Brand Pending",
            kind="manual",
            status="pending",
            rights_display=True,
            rights_tryon=False,
            image_policy="hotlink",
        )
        session.add_all([s1, s2])

        # 2. Merchant
        m = Merchant(id=uuid4(), name="Test Merchant", merchant_type="brand")
        session.add(m)

        # 3. Products
        p1 = MerchantProduct(
            id=uuid4(),
            merchant_id=m.id,
            source_id=s1.id,
            source_product_id="sku-1",
            title="Silk Shirt",
            source_url="https://merchant.example/p1",
            status="active",
        )
        p2 = MerchantProduct(
            id=uuid4(),
            merchant_id=m.id,
            source_id=s2.id,
            source_product_id="sku-2",
            title="Sneakers",
            source_url="https://merchant.example/p2",
            status="active",
        )
        p3 = MerchantProduct(
            id=uuid4(),
            merchant_id=m.id,
            source_id=s1.id,
            source_product_id="sku-3",
            title="Shoes Cleared",
            source_url="https://merchant.example/p3",
            status="active",
        )
        session.add_all([p1, p2, p3])

        # 4. Garments
        g1 = CanonicalGarment(id=uuid4(), category="tops", tryon_supported=False)
        g2 = CanonicalGarment(id=uuid4(), category="shoes", tryon_supported=False)
        g3 = CanonicalGarment(id=uuid4(), category="bottoms", tryon_supported=False)
        session.add_all([g1, g2, g3])

        # 5. Offers
        o1 = MerchantOffer(
            id=uuid4(),
            garment_id=g1.id,
            merchant_id=m.id,
            source_product_id="sku-1",
            url="https://merchant.example/p1",
            price_minor=1000,
        )
        o2 = MerchantOffer(
            id=uuid4(),
            garment_id=g2.id,
            merchant_id=m.id,
            source_product_id="sku-3",
            url="https://merchant.example/p3",
            price_minor=2000,
        )
        o3 = MerchantOffer(
            id=uuid4(),
            garment_id=g3.id,
            merchant_id=m.id,
            source_product_id="sku-2",
            url="https://merchant.example/p2",
            price_minor=3000,
        )
        session.add_all([o1, o2, o3])

        # 6. Enrichments: g1 is enriched as tryon_suitable with confidence 0.95
        e1 = GarmentEnrichment(
            id=uuid4(),
            garment_id=g1.id,
            model_version="vlm-v1",
            attributes_json={"tryon_suitable": True, "category": "tops"},
            confidence_summary={"tryon_suitable": 0.95, "category": 0.95},
        )
        # g2 is enriched but category is shoes
        e2 = GarmentEnrichment(
            id=uuid4(),
            garment_id=g2.id,
            model_version="vlm-v1",
            attributes_json={"tryon_suitable": True, "category": "shoes"},
            confidence_summary={"tryon_suitable": 0.95, "category": 0.95},
        )
        session.add_all([e1, e2])
        await session.commit()

        # Step A: Dry run (default) should report 1 update needed, but NOT modify DB
        dry_stats = await backfill_tryon_supported(session, dry_run=True)
        assert dry_stats["dry_run"] is True
        assert dry_stats["eligible"] == 1
        assert dry_stats["updated"] == 1

        await session.refresh(g1)
        assert g1.tryon_supported is False, "Dry run must NOT mutate garments"

        # Step B: Apply mode modifies DB
        apply_stats = await backfill_tryon_supported(session, dry_run=False)
        assert apply_stats["dry_run"] is False
        assert apply_stats["eligible"] == 1
        assert apply_stats["updated"] == 1

        await session.refresh(g1)
        await session.refresh(g2)
        await session.refresh(g3)
        assert g1.tryon_supported is True
        assert g2.tryon_supported is False
        assert g3.tryon_supported is False

    await engine.dispose()
