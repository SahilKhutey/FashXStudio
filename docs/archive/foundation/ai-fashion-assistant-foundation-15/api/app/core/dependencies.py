from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db_session
from api.app.catalog.repositories.catalog import CatalogRepository
from api.app.profile.repositories.profile import ProfileRepository


async def db_session(session: AsyncSession = Depends(get_db_session)) -> AsyncIterator[AsyncSession]:
    yield session


def profile_repository(session: AsyncSession = Depends(get_db_session)) -> ProfileRepository:
    return ProfileRepository(session)


def catalog_repository(session: AsyncSession = Depends(get_db_session)) -> CatalogRepository:
    return CatalogRepository(session)


def profile_media_repository(session: AsyncSession = Depends(get_db_session)):
    from api.app.profile.repositories.media import ProfileMediaRepository
    return ProfileMediaRepository(session)


def object_storage():
    from api.app.profile.integrations.r2_client import R2StorageClient
    return R2StorageClient()


def profile_photo_queue():
    from api.app.profile.integrations.redis_queue import RedisQueue
    return RedisQueue()


def profile_photo_job_repository(session: AsyncSession = Depends(get_db_session)):
    from api.app.profile.repositories.media_jobs import ProfilePhotoJobRepository
    return ProfilePhotoJobRepository(session)


def profile_intelligence_repository(session: AsyncSession = Depends(get_db_session)):
    from api.app.profile.repositories.intelligence import ProfileIntelligenceRepository
    return ProfileIntelligenceRepository(session)
