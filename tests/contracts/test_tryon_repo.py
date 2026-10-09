from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.catalog import CanonicalGarment, Merchant, MerchantProduct
from database.models.identity import User, UserPhoto
from database.models.tryon import TryOnJob
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork


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
async def test_tryon_job_and_artifact_lifecycle(session_factory) -> None:
    uow = TryOnUnitOfWork(session_factory)
    user_id = uuid4()
    garment_id = uuid4()
    photo_id = uuid4()
    job_id = uuid4()

    async with uow:
        # Seed parent records
        uow.session.add(User(id=user_id))
        merchant = Merchant(id=uuid4(), name="Test Merchant", merchant_type="affiliate")
        uow.session.add(merchant)
        mp = MerchantProduct(
            id=uuid4(),
            merchant_id=merchant.id,
            source_product_id="P1",
            title="T-Shirt",
            source_url="https://example.com/p1",
        )
        uow.session.add(mp)
        garment = CanonicalGarment(
            id=garment_id,
            category="tops",
        )
        uow.session.add(garment)
        photo = UserPhoto(
            id=photo_id,
            user_id=user_id,
            photo_type="full_body",
            storage_key="photos/1.png",
            status="accepted",
        )
        uow.session.add(photo)

        job = TryOnJob(
            id=job_id,
            user_id=user_id,
            garment_id=garment_id,
            profile_photo_id=photo_id,
            idempotency_key="idemp-1",
            artifact_key="art-1",
            status="queued",
            model_version="v1.0",
            pipeline_version="p1.0",
        )
        uow.jobs.add(job)
        await uow.commit()

    # Verify retrieval
    verify_uow = TryOnUnitOfWork(session_factory)
    async with verify_uow:
        retrieved = await verify_uow.jobs.get_by_id(job_id)
        assert retrieved is not None
        assert retrieved.status == "queued"
        assert retrieved.artifact_key == "art-1"

        # Claim next job
        claimed = await verify_uow.jobs.claim_next_job(worker_id="worker-1")
        assert claimed is not None
        assert claimed.id == job_id
        assert claimed.status == "running"

        # Update status
        updated = await verify_uow.jobs.update_status(job_id=job_id, status="completed")
        assert updated is not None
        assert updated.status == "completed"
        assert updated.completed_at is not None
        await verify_uow.commit()
