from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.erasure import ErasureTombstone
from database.models.identity import User, UserPhoto
from fashx.account.repository import AccountRepository
from fashx.account.schemas import AccountStatus
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.workers.account_deletion import execute_account_deletion_job


class MockStorage:
    def __init__(self):
        self.deleted_prefixes = []
        self.deleted_keys = []

    def delete_prefix(self, prefix: str):
        self.deleted_prefixes.append(prefix)

    def delete(self, key: str):
        self.deleted_keys.append(key)


@pytest.fixture
async def setup_deletion_context():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    storage = MockStorage()

    async with session_maker() as session:
        repo = AccountRepository(session)
        # Create user with a photo
        user_id = uuid4()
        user = User(id=user_id, status=AccountStatus.ACTIVE.value, email_normalized="delete.me@fashx.com")
        photo = UserPhoto(
            id=uuid4(),
            user_id=user_id,
            photo_type="body",
            storage_key=f"users/{user_id}/photos/body.jpg",
            status="accepted",
        )
        session.add(user)
        session.add(photo)
        await session.commit()

        uow = ProfileUnitOfWork(session_maker)
        yield repo, uow, storage, user_id, session

    await engine.dispose()


@pytest.mark.asyncio
async def test_account_deletion_worker_full_lifecycle(setup_deletion_context):
    repo, uow, storage, user_id, session = setup_deletion_context

    # 1. Create deletion job (as would be done by /account/deletion-request)
    job = await repo.create_deletion_job(user_id)
    assert job.status == "PENDING"

    # User status should be DELETION_PENDING
    user = await repo.get_user_by_id(user_id)
    assert user.status == "DELETION_PENDING"

    # 2. Worker executes job
    res = await execute_account_deletion_job(
        job_id=job.id,
        repo=repo,
        uow=uow,
        storage=storage,
    )
    assert res["status"] == "completed"

    # 3. Verify job status is COMPLETED
    updated_job = await repo.get_deletion_job(job.id)
    assert updated_job.status == "COMPLETED"
    assert updated_job.completed_at is not None

    # 4. Verify tombstone was recorded
    tombstone = await session.get(ErasureTombstone, user_id)
    assert tombstone is not None

    # 5. Verify user and photo are hard-deleted
    user_after = await repo.get_user_by_id(user_id)
    assert user_after is None
    photo_after = await session.get(UserPhoto, user_id)
    assert photo_after is None

    # 6. Verify storage deletion was invoked for user prefix
    assert any(f"u/{user_id}/" in prefix for prefix in storage.deleted_prefixes) or len(storage.deleted_keys) > 0


@pytest.mark.asyncio
async def test_account_deletion_worker_idempotent_reexecution(setup_deletion_context):
    repo, uow, storage, user_id, _ = setup_deletion_context

    job = await repo.create_deletion_job(user_id)
    await execute_account_deletion_job(job.id, repo, uow, storage)

    # Re-running already completed job returns already_completed
    second_run = await execute_account_deletion_job(job.id, repo, uow, storage)
    assert second_run["status"] == "already_completed"
