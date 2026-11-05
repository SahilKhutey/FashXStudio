from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import (
    CanonicalGarment,
    CatalogSource,
    Merchant,
    MerchantOffer,
    MerchantProduct,
)
from database.models.identity import User
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.application.create_buy_click import (
    CreateBuyClickCommand,
    CreateBuyClickUseCase,
)
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.core.errors import EntityNotFoundError, ValidationError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


@pytest.fixture
async def db_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_rc06_successful_buy_click(db_session_factory):
    user_id = uuid4()
    garment_id = uuid4()
    merchant_id = uuid4()
    source_id = uuid4()
    offer_id = uuid4()

    profile_uow = ProfileUnitOfWork(db_session_factory)
    catalog_uow = CatalogUnitOfWork(db_session_factory)
    commerce_uow = CommerceWardrobeUnitOfWork(db_session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        merchant = Merchant(id=merchant_id, name="Test Myntra", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)

        source = CatalogSource(
            id=source_id,
            slug=f"src-{merchant_id}",
            name="Myntra Feed",
            kind="manual",
            status="cleared",
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.sources.add(source)

        garment = CanonicalGarment(
            id=garment_id,
            display_name="Oxford Cotton Shirt",
            category="tops",
            subcategory="shirts",
            active=True,
            price_minor=129900,
        )
        catalog_uow.canonical_garments.add(garment)

        product = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant_id,
            source_id=source_id,
            source_product_id="PROD-001",
            title="Oxford Cotton Shirt Blue",
            source_url="https://www.myntra.com/shirts/oxford-cotton-blue",
        )
        catalog_uow.merchant_products.add(product)

        offer = MerchantOffer(
            id=offer_id,
            garment_id=garment_id,
            merchant_id=merchant_id,
            source_product_id="PROD-001",
            url="https://www.myntra.com/shirts/oxford-cotton-blue",
            price_minor=129900,
            currency="INR",
            in_stock=True,
        )
        catalog_uow.offers.add(offer)
        await catalog_uow.commit()

    use_case = CreateBuyClickUseCase(
        commerce_uow=commerce_uow,
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        allowed_hosts={"myntra.com"},
    )

    cmd = CreateBuyClickCommand(
        user_id=user_id,
        garment_id=garment_id,
        offer_id=offer_id,
    )
    result = await use_case.execute(cmd)

    assert result.buy_click_id is not None
    assert result.tracking_id.startswith(f"fashx_{user_id.hex[:8]}_")

    parsed = urlparse(result.redirect_url)
    assert parsed.scheme == "https"
    assert parsed.hostname == "www.myntra.com"
    qs = parse_qs(parsed.query)
    assert qs["utm_source"] == ["fashx"]
    assert qs["utm_medium"] == ["app"]
    assert qs["utm_campaign"] == ["vto_purchase"]
    assert qs["sub_id"] == [result.tracking_id]
    assert qs["click_id"] == [str(result.buy_click_id)]

    # Verify click was persisted in DB
    async with commerce_uow:
        persisted = await commerce_uow.buy_clicks.get_by_id(result.buy_click_id)
        assert persisted is not None
        assert persisted.offer_id == offer_id
        assert persisted.garment_id == garment_id
        assert persisted.user_id == user_id


@pytest.mark.asyncio
async def test_rc06_buy_click_user_not_found(db_session_factory):
    use_case = CreateBuyClickUseCase(
        commerce_uow=CommerceWardrobeUnitOfWork(db_session_factory),
        profile_uow=ProfileUnitOfWork(db_session_factory),
        catalog_uow=CatalogUnitOfWork(db_session_factory),
    )
    with pytest.raises(EntityNotFoundError) as exc:
        await use_case.execute(
            CreateBuyClickCommand(
                user_id=uuid4(),
                garment_id=uuid4(),
                offer_id=uuid4(),
            )
        )
    assert "User" in str(exc.value)


@pytest.mark.asyncio
async def test_rc06_buy_click_garment_not_found(db_session_factory):
    user_id = uuid4()
    profile_uow = ProfileUnitOfWork(db_session_factory)
    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    use_case = CreateBuyClickUseCase(
        commerce_uow=CommerceWardrobeUnitOfWork(db_session_factory),
        profile_uow=profile_uow,
        catalog_uow=CatalogUnitOfWork(db_session_factory),
    )
    with pytest.raises(EntityNotFoundError) as exc:
        await use_case.execute(
            CreateBuyClickCommand(
                user_id=user_id,
                garment_id=uuid4(),
                offer_id=uuid4(),
            )
        )
    assert "CanonicalGarment" in str(exc.value)


@pytest.mark.asyncio
async def test_rc06_buy_click_inactive_garment(db_session_factory):
    user_id = uuid4()
    garment_id = uuid4()
    profile_uow = ProfileUnitOfWork(db_session_factory)
    catalog_uow = CatalogUnitOfWork(db_session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        garment = CanonicalGarment(
            id=garment_id,
            display_name="Archived Jacket",
            category="outerwear",
            active=False,
            price_minor=499900,
        )
        catalog_uow.canonical_garments.add(garment)
        await catalog_uow.commit()

    use_case = CreateBuyClickUseCase(
        commerce_uow=CommerceWardrobeUnitOfWork(db_session_factory),
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )
    with pytest.raises(ValidationError) as exc:
        await use_case.execute(
            CreateBuyClickCommand(
                user_id=user_id,
                garment_id=garment_id,
                offer_id=uuid4(),
            )
        )
    assert "inactive" in str(exc.value)


@pytest.mark.asyncio
async def test_rc06_buy_click_offer_mismatch(db_session_factory):
    user_id = uuid4()
    garment_a_id = uuid4()
    garment_b_id = uuid4()
    merchant_id = uuid4()
    offer_id = uuid4()

    profile_uow = ProfileUnitOfWork(db_session_factory)
    catalog_uow = CatalogUnitOfWork(db_session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        catalog_uow.canonical_garments.add(
            CanonicalGarment(id=garment_a_id, display_name="Garment A", category="tops", active=True, price_minor=1000)
        )
        catalog_uow.canonical_garments.add(
            CanonicalGarment(id=garment_b_id, display_name="Garment B", category="tops", active=True, price_minor=2000)
        )
        catalog_uow.merchants.add(Merchant(id=merchant_id, name="Store", merchant_type="retailer"))
        # Offer belongs to garment B
        catalog_uow.offers.add(
            MerchantOffer(
                id=offer_id,
                garment_id=garment_b_id,
                merchant_id=merchant_id,
                source_product_id="PROD-B",
                url="https://www.store.com/item",
                price_minor=2000,
                in_stock=True,
            )
        )
        await catalog_uow.commit()

    use_case = CreateBuyClickUseCase(
        commerce_uow=CommerceWardrobeUnitOfWork(db_session_factory),
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )
    with pytest.raises(ValidationError) as exc:
        await use_case.execute(
            CreateBuyClickCommand(
                user_id=user_id,
                garment_id=garment_a_id,  # requesting with Garment A
                offer_id=offer_id,
            )
        )
    assert "does not belong" in str(exc.value)


@pytest.mark.asyncio
async def test_rc06_buy_click_out_of_stock(db_session_factory):
    user_id = uuid4()
    garment_id = uuid4()
    merchant_id = uuid4()
    offer_id = uuid4()

    profile_uow = ProfileUnitOfWork(db_session_factory)
    catalog_uow = CatalogUnitOfWork(db_session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        catalog_uow.canonical_garments.add(
            CanonicalGarment(id=garment_id, display_name="Garment", category="tops", active=True, price_minor=1000)
        )
        catalog_uow.merchants.add(Merchant(id=merchant_id, name="Store", merchant_type="retailer"))
        catalog_uow.offers.add(
            MerchantOffer(
                id=offer_id,
                garment_id=garment_id,
                merchant_id=merchant_id,
                source_product_id="PROD-1",
                url="https://www.store.com/item",
                price_minor=1000,
                in_stock=False,  # Out of stock
            )
        )
        await catalog_uow.commit()

    use_case = CreateBuyClickUseCase(
        commerce_uow=CommerceWardrobeUnitOfWork(db_session_factory),
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
    )
    with pytest.raises(ValidationError) as exc:
        await use_case.execute(
            CreateBuyClickCommand(
                user_id=user_id,
                garment_id=garment_id,
                offer_id=offer_id,
            )
        )
    assert "out of stock" in str(exc.value)


@pytest.mark.asyncio
async def test_rc06_buy_click_uncleared_catalog_source(db_session_factory):
    user_id = uuid4()
    garment_id = uuid4()
    merchant_id = uuid4()
    source_id = uuid4()
    offer_id = uuid4()

    profile_uow = ProfileUnitOfWork(db_session_factory)
    catalog_uow = CatalogUnitOfWork(db_session_factory)

    async with profile_uow:
        profile_uow.users.add(User(id=user_id))
        await profile_uow.commit()

    async with catalog_uow:
        catalog_uow.canonical_garments.add(
            CanonicalGarment(id=garment_id, display_name="Garment", category="tops", active=True, price_minor=1000)
        )
        catalog_uow.merchants.add(Merchant(id=merchant_id, name="Store", merchant_type="retailer"))
        source = CatalogSource(
            id=source_id,
            slug="store-feed",
            name="Store Feed",
            kind="manual",
            status="pending",  # NOT CLEARED
            rights_display=True,
            rights_tryon=True,
            image_policy="mirror",
        )
        catalog_uow.sources.add(source)
        catalog_uow.merchant_products.add(
            MerchantProduct(
                id=uuid4(),
                merchant_id=merchant_id,
                source_id=source_id,
                source_product_id="PROD-1",
                title="Garment",
                source_url="https://www.store.com/item",
            )
        )
        catalog_uow.offers.add(
            MerchantOffer(
                id=offer_id,
                garment_id=garment_id,
                merchant_id=merchant_id,
                source_product_id="PROD-1",
                url="https://www.store.com/item",
                price_minor=1000,
                in_stock=True,
            )
        )
        await catalog_uow.commit()

    use_case = CreateBuyClickUseCase(
        commerce_uow=CommerceWardrobeUnitOfWork(db_session_factory),
        profile_uow=profile_uow,
        catalog_uow=catalog_uow,
        allowed_hosts={"store.com"},
    )
    with pytest.raises(ValidationError) as exc:
        await use_case.execute(
            CreateBuyClickCommand(
                user_id=user_id,
                garment_id=garment_id,
                offer_id=offer_id,
            )
        )
    assert "not cleared" in str(exc.value)
