from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment
from database.models.commerce_feedback import WardrobeItem
from database.models.identity import User
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)


@pytest_asyncio.fixture
async def session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_wardrobe_price_snapshot_and_retrieval(session_factory) -> None:
    uow = CommerceWardrobeUnitOfWork(session_factory)
    user_id = uuid4()
    garment_id = uuid4()
    item_id = uuid4()

    async with uow:
        uow.session.add(User(id=user_id))
        garment = CanonicalGarment(id=garment_id, category="outerwear")
        uow.session.add(garment)

        item = WardrobeItem(
            id=item_id,
            user_id=user_id,
            garment_id=garment_id,
            snapshot_title="Classic Blazer",
            snapshot_price_minor=299900,
            snapshot_currency="INR",
            snapshot_image_key="garments/blazer.png",
        )
        uow.wardrobe.add(item)
        await uow.commit()

    verify_uow = CommerceWardrobeUnitOfWork(session_factory)
    async with verify_uow:
        items = await verify_uow.wardrobe.list_for_user(user_id)
        assert len(items) == 1
        assert items[0].snapshot_price_minor == 299900
        assert items[0].snapshot_currency == "INR"
        assert items[0].snapshot_title == "Classic Blazer"

        by_garment = await verify_uow.wardrobe.get_by_user_and_garment(user_id, garment_id)
        assert by_garment is not None
        assert by_garment.id == item_id
