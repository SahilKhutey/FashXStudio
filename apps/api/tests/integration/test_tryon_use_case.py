"""
Integration Tests: StartTryOnUseCase & Atomic Job Claiming (Rule I07 & I09)
"""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.application.use_cases.start_tryon import StartTryOnCommand, StartTryOnUseCase
from app.infrastructure.queue.local_queue import LocalJobQueueAdapter
from app.repositories.models import Base, CanonicalGarmentModel, UserModel
from app.repositories.tryon_repo import TryOnRepository


@pytest_asyncio.fixture
async def async_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_start_tryon_and_atomic_claim(async_db_session):
    # Setup initial mock user and garment
    user_id = uuid.uuid4()
    garment_id = uuid.uuid4()

    user = UserModel(
        user_id=user_id,
        email="test@fashx.studio",
        password_hash="fake_hash",
    )
    garment = CanonicalGarmentModel(
        canonical_id=garment_id,
        category="topwear",
        subcategory="overshirt",
        gender_target="men",
        silhouette="relaxed",
        primary_color="olive_green",
        color_hex="#4B5320",
        color_palette_type="warm_earth",
        material="cotton",
    )
    async_db_session.add_all([user, garment])
    await async_db_session.commit()

    repo = TryOnRepository(async_db_session)
    queue = LocalJobQueueAdapter()
    use_case = StartTryOnUseCase(tryon_repo=repo, queue=queue)

    cmd = StartTryOnCommand(
        user_id=user_id,
        canonical_garment_id=garment_id,
        user_photo_id="photo_123",
        user_photo_hash="hash_photo_123",
        canonical_garment_version=1,
        model_adapter_id="idm_vton_v1",
        model_weights_version="weights_2026_08",
        preprocessing_version="sam_bisenet_v2",
        render_config_hash="cfg_default",
    )

    # 1. First execution: Cache miss -> Queued
    res1 = await use_case.execute(cmd)
    assert res1.status == "queued"
    assert res1.cache_hit is False

    # 2. Rule I07: Atomic Job Claiming
    # Worker A claims job
    claimed_by_worker_a = await repo.claim_job_atomically(
        job_id=res1.job_id,
        worker_id="worker_gpu_node_1",
    )
    assert claimed_by_worker_a is not None
    assert claimed_by_worker_a.status == "processing"
    assert claimed_by_worker_a.worker_id == "worker_gpu_node_1"

    # Worker B tries to claim the same job concurrently -> must fail (returns None)
    claimed_by_worker_b = await repo.claim_job_atomically(
        job_id=res1.job_id,
        worker_id="worker_gpu_node_2",
    )
    assert claimed_by_worker_b is None  # Atomically blocked!

    # Complete the job
    await repo.complete_job(
        job_id=res1.job_id,
        result_image_url="https://cdn.fashx.studio/renders/render_101.webp",
        inference_ms=2800,
    )

    # 3. Rule I09: Second execution with same parameters -> Cache Hit
    res2 = await use_case.execute(cmd)
    assert res2.status == "completed"
    assert res2.cache_hit is True
    assert res2.result_image_url == "https://cdn.fashx.studio/renders/render_101.webp"
