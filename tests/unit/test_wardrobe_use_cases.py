from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.catalog.application.ingest_product import (
    IngestMerchantProductUseCase,
    IngestProductCommand,
)
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.application.list_wardrobe import ListWardrobeUseCase
from fashx.commerce_wardrobe.application.remove_from_wardrobe import (
    RemoveFromWardrobeUseCase,
)
from fashx.commerce_wardrobe.application.save_to_wardrobe import (
    SaveToWardrobeCommand,
    SaveToWardrobeUseCase,
)
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.core.errors import EntityNotFoundError
from fashx.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from database.models.catalog import Merchant


@pytest.mark.asyncio
async def test_wardrobe_save_list_and_remove(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    profile_uow = ProfileUnitOfWork(session_factory)
    catalog_uow = CatalogUnitOfWork(session_factory)
    wardrobe_uow = CommerceWardrobeUnitOfWork(session_factory)

    # 1. Create User
    create_uc = CreateProfileUseCase(profile_uow)
    user_res = await create_uc.execute(CreateProfileCommand(height_cm=178, weight_kg=72))
    user_id = user_res.user_id

    # 2. Ingest Garment with Offer
    async with catalog_uow:
        merchant = Merchant(name="Closet Merchant", merchant_type="retailer")
        catalog_uow.merchants.add(merchant)
        await catalog_uow.commit()
        merchant_id = merchant.id

    ingest_uc = IngestMerchantProductUseCase(catalog_uow)
    product_res = await ingest_uc.execute(
        IngestProductCommand(
            merchant_id=merchant_id,
            source_product_id="ITEM-WARDROBE-1",
            title="Vintage Suede Bomber Jacket",
            source_url="https://merchant.com/bomber",
            category="outerwear",
            price_minor=499900,
        )
    )
    garment_id = product_res.canonical_garment_id

    # 3. Save to Wardrobe (Rule I11: Snapshotting)
    save_uc = SaveToWardrobeUseCase(wardrobe_uow, profile_uow, catalog_uow)
    dummy_artifact_id = uuid4()
    save_res = await save_uc.execute(
        SaveToWardrobeCommand(
            user_id=user_id,
            garment_id=garment_id,
            tryon_artifact_id=dummy_artifact_id,
        )
    )

    assert save_res.user_id == user_id
    assert save_res.garment_id == garment_id
    assert save_res.snapshot_price_minor == 499900
    assert save_res.snapshot_currency == "INR"
    assert "Vintage Suede Bomber Jacket" in save_res.snapshot_title
    assert save_res.tryon_artifact_id == dummy_artifact_id

    # 4. List User Wardrobe
    list_uc = ListWardrobeUseCase(wardrobe_uow)
    items = await list_uc.execute(user_id)
    assert len(items) == 1
    assert items[0].item_id == save_res.item_id
    assert items[0].snapshot_price_minor == 499900

    # 5. Remove from Wardrobe
    remove_uc = RemoveFromWardrobeUseCase(wardrobe_uow)
    removed = await remove_uc.execute(user_id=user_id, item_id=save_res.item_id)
    assert removed is True

    items_after = await list_uc.execute(user_id)
    assert len(items_after) == 0

    # 6. Removing non-existent item raises EntityNotFoundError
    with pytest.raises(EntityNotFoundError):
        await remove_uc.execute(user_id=user_id, item_id=save_res.item_id)
