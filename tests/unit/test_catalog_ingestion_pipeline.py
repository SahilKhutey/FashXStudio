"""Unit tests for the catalog ingestion pipeline, safe HTTP fetching, parsers, idempotency, and takedown."""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import (
    CatalogSource,
    CategoryMap,
    MerchantOffer,
    MerchantProduct,
)
from fashx.infrastructure.storage.local import LocalStorage
from fashx.ingest.dedup import evaluate_dedup
from fashx.ingest.google_feed import map_row, rows_from_csv, rows_from_xml
from fashx.ingest.normalizer import (
    normalize_color,
    normalize_size,
    validate_age_group,
)
from fashx.ingest.pipeline import IngestPipeline
from fashx.ingest.safe_http import Reject, assert_public_https


def test_safe_http_ssrf_rejection() -> None:
    # Non-HTTPS
    with pytest.raises(Reject) as exc:
        assert_public_https("http://example.com/feed.csv")
    assert exc.value.code == "non_https_url"

    # Loopback / Localhost
    with pytest.raises(Reject) as exc:
        assert_public_https("https://127.0.0.1/feed.csv")
    assert exc.value.code == "private_address"

    with pytest.raises(Reject) as exc:
        assert_public_https("https://localhost/feed.csv")
    assert exc.value.code == "private_address"

    # Cloud metadata link-local
    with pytest.raises(Reject) as exc:
        assert_public_https("https://169.254.169.254/latest/meta-data")
    assert exc.value.code == "private_address"

    # RFC 1918 Private ranges
    with pytest.raises(Reject) as exc:
        assert_public_https("https://10.0.0.5/image.jpg")
    assert exc.value.code == "private_address"

    with pytest.raises(Reject) as exc:
        assert_public_https("https://192.168.1.100/feed.xml")
    assert exc.value.code == "private_address"


def test_parsers_csv_and_xml() -> None:
    # CSV with UTF-8 BOM and quotes
    csv_bytes = (
        "\ufeffid,title,description,price,link,image_link,availability,gender,age_group\n"
        'SKU-1,"Embroidered Silk Kurta","Traditional festive wear","2499 INR",https://brand.com/p1,https://brand.com/i1.jpg,in_stock,female,adult\n'
        'SKU-2,"Slim Chino Pants","Cotton casual trousers","1799 INR",https://brand.com/p2,https://brand.com/i2.jpg,in_stock,male,adult\n'
    ).encode("utf-8")

    rows = list(rows_from_csv(csv_bytes))
    assert len(rows) == 2
    assert rows[0]["id"] == "SKU-1"
    assert rows[0]["title"] == "Embroidered Silk Kurta"

    p1 = map_row(rows[0])
    assert p1.price == Decimal("2499")
    assert p1.currency == "INR"
    assert p1.gender == "female"

    # Kids exclusion
    with pytest.raises(Reject) as exc:
        validate_age_group("kids")
    assert exc.value.code == "out_of_scope"

    # XML feed parsing via defusedxml
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <item>
          <id>XML-101</id>
          <title>Printed Cotton Shirt</title>
          <price>1299 INR</price>
          <link>https://brand.com/shirt</link>
          <image_link>https://brand.com/shirt.jpg</image_link>
          <availability>in stock</availability>
        </item>
      </channel>
    </rss>
    """
    xml_rows = list(rows_from_xml(xml_bytes))
    assert len(xml_rows) == 1
    assert xml_rows[0]["id"] == "XML-101"
    assert xml_rows[0]["title"] == "Printed Cotton Shirt"


def test_normalizers() -> None:
    # Color mapping
    _, fam1 = normalize_color("Deep Mehendi Green")
    assert fam1 == "green"
    _, fam2 = normalize_color("Royal Maroon")
    assert fam2 == "red"
    _, fam3 = normalize_color("Mustard Yellow")
    assert fam3 == "yellow"
    _, fam4 = normalize_color("Midnight Navy")
    assert fam4 == "blue"

    # Size normalization
    _, s1 = normalize_size("Medium")
    assert s1 == "M"
    _, s2 = normalize_size("38 (M)")
    assert s2 == "M"
    _, s3 = normalize_size("Free Size")
    assert s3 == "Free Size"
    _, s4 = normalize_size("UK 10")
    assert s4 == "UK 10"
    _, s5 = normalize_size("32")
    assert s5 == "32"


def test_dedup_variant_and_perceptual_hash() -> None:
    existing = [
        {
            "source_product_id": "BASE-RED",
            "item_group_id": "GROUP-KURTA",
            "image_sha256": "aabbcc112233",
            "image_dhash": "0000000000000000",
            "brand": "FabIndia",
            "category": "kurtas",
            "canonical_garment_id": "00000000-0000-0000-0000-000000000001",
        }
    ]

    # 1. Variant grouping via item_group_id
    dec_variant = evaluate_dedup(
        source_product_id="BASE-BLUE",
        item_group_id="GROUP-KURTA",
        image_sha256="different_sha",
        image_dhash="ffffffffffffffff",
        brand="FabIndia",
        category="kurtas",
        existing_records=existing,
    )
    assert dec_variant.action == "variant_group"
    assert dec_variant.canonical_id == "00000000-0000-0000-0000-000000000001"

    # 2. Exact match via SHA-256
    dec_exact = evaluate_dedup(
        source_product_id="DUPE-RED",
        item_group_id=None,
        image_sha256="aabbcc112233",
        image_dhash=None,
        brand="FabIndia",
        category="kurtas",
        existing_records=existing,
    )
    assert dec_exact.action == "exact_match"

    # 3. Perceptual dHash near match (distance 2 <= 4)
    dec_perc = evaluate_dedup(
        source_product_id="NEAR-KURTA",
        item_group_id=None,
        image_sha256="other_sha",
        image_dhash="0000000000000003",  # 2 bit difference from 0000000000000000
        brand="FabIndia",
        category="kurtas",
        existing_records=existing,
        max_dhash_distance=4,
    )
    assert dec_perc.action == "perceptual_match"
    assert dec_perc.hamming_distance == 2


@pytest.mark.asyncio
async def test_pipeline_idempotency_and_change_detection(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)

    async with session_factory() as session:
        # Create cleared source
        source = CatalogSource(
            slug="brand-pilot",
            name="Brand Pilot",
            kind="feed_url",
            status="cleared",
            rights_display=True,
            rights_tryon=False,
            image_policy="hotlink",
            refresh_hours=24,
            max_rps=5.0,
        )
        session.add(source)
        await session.commit()

        # Seed category mapping
        cat_map = CategoryMap(
            source_id=source.id,
            source_category="Ethnic Wear > Kurtas",
            taxonomy_id="kurtas",
        )
        session.add(cat_map)
        await session.commit()

    # Feed with 2 products
    feed_csv_1 = (
        b"id,title,description,price,link,image_link,availability,product_type\n"
        b"P1,Cotton Kurta,Classic kurta,1499 INR,https://pilot.com/p1,https://pilot.com/i1.jpg,in_stock,Ethnic Wear > Kurtas\n"
        b"P2,Linen Shirt,Casual shirt,1999 INR,https://pilot.com/p2,https://pilot.com/i2.jpg,in_stock,Ethnic Wear > Kurtas\n"
    )

    # Run 1: First ingestion -> 2 new products
    async with session_factory() as session:
        pipeline = IngestPipeline(session, storage=storage)
        run1 = await pipeline.run(source_slug="brand-pilot", feed_data=feed_csv_1)
        assert run1.status == "ok"
        assert run1.counts["new"] == 2
        assert run1.counts["unchanged"] == 0

    # Run 2: Exact same feed -> Idempotency check: 0 new, 2 unchanged
    async with session_factory() as session:
        pipeline = IngestPipeline(session, storage=storage)
        run2 = await pipeline.run(source_slug="brand-pilot", feed_data=feed_csv_1)
        assert run2.status == "ok"
        assert run2.counts["new"] == 0
        assert run2.counts["updated"] == 0
        assert run2.counts["unchanged"] == 2

    # Run 3: Price changed on P1 from 1499 to 1299 -> 1 updated, 1 unchanged
    feed_csv_2 = (
        b"id,title,description,price,link,image_link,availability,product_type\n"
        b"P1,Cotton Kurta,Classic kurta,1299 INR,https://pilot.com/p1,https://pilot.com/i1.jpg,in_stock,Ethnic Wear > Kurtas\n"
        b"P2,Linen Shirt,Casual shirt,1999 INR,https://pilot.com/p2,https://pilot.com/i2.jpg,in_stock,Ethnic Wear > Kurtas\n"
    )

    async with session_factory() as session:
        pipeline = IngestPipeline(session, storage=storage)
        run3 = await pipeline.run(source_slug="brand-pilot", feed_data=feed_csv_2)
        assert run3.status == "ok"
        assert run3.counts["new"] == 0
        assert run3.counts["updated"] == 1
        assert run3.counts["unchanged"] == 1

        # Verify updated price in offer
        p1_offer = (
            await session.scalars(
                select(MerchantOffer).where(MerchantOffer.source_product_id == "P1")
            )
        ).first()
        assert p1_offer is not None
        assert p1_offer.price_minor == 129900


@pytest.mark.asyncio
async def test_mass_removal_guard(
    session_factory: async_sessionmaker[AsyncSession],
    tmp_path,
) -> None:
    storage = LocalStorage(tmp_path)

    async with session_factory() as session:
        source = CatalogSource(
            slug="brand-large",
            name="Brand Large",
            kind="feed_url",
            status="cleared",
            rights_display=True,
            rights_tryon=False,
            image_policy="hotlink",
        )
        session.add(source)
        await session.commit()

    # Create 12 products in run 1
    csv_rows = ["id,title,price,link,image_link,availability"]
    for i in range(12):
        csv_rows.append(f"SKU-{i},Product {i},999 INR,https://large.com/p{i},https://large.com/i{i}.jpg,in_stock")
    feed_12 = "\n".join(csv_rows).encode("utf-8")

    async with session_factory() as session:
        pipeline = IngestPipeline(session, storage=storage)
        run1 = await pipeline.run(source_slug="brand-large", feed_data=feed_12)
        assert run1.status == "ok"
        assert run1.counts["new"] == 12

    # Run 2: Feed is truncated/broken, sees only 3 items (< 50% of 12)
    broken_feed = (
        b"id,title,price,link,image_link,availability\n"
        b"SKU-0,Product 0,999 INR,https://large.com/p0,https://large.com/i0.jpg,in_stock\n"
        b"SKU-1,Product 1,999 INR,https://large.com/p1,https://large.com/i1.jpg,in_stock\n"
        b"SKU-2,Product 2,999 INR,https://large.com/p2,https://large.com/i2.jpg,in_stock\n"
    )

    async with session_factory() as session:
        pipeline = IngestPipeline(session, storage=storage)
        run2 = await pipeline.run(source_slug="brand-large", feed_data=broken_feed)
        # Mass removal guard must trigger and abort the run!
        assert run2.status == "aborted"
        assert "mass_removal_guard" in (run2.error or "")

        # Verify all 12 products remain active and not removed
        all_prods = (
            await session.scalars(
                select(MerchantProduct).where(MerchantProduct.source_id == run2.source_id)
            )
        ).all()
        assert len(all_prods) == 12
        for p in all_prods:
            assert p.status == "active"
