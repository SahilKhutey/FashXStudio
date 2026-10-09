from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db_session
from fashx.catalog.repositories.catalog import CatalogRepository
from fashx.profile.repositories.profile import ProfileRepository


async def db_session(session: AsyncSession = Depends(get_db_session)) -> AsyncIterator[AsyncSession]:
    yield session


def profile_repository(session: AsyncSession = Depends(get_db_session)) -> ProfileRepository:
    return ProfileRepository(session)


def catalog_repository(session: AsyncSession = Depends(get_db_session)) -> CatalogRepository:
    return CatalogRepository(session)


def get_storage() -> "ObjectStorage":
    from fashx.application.ports.storage import ObjectStorage
    from fashx.infrastructure.storage.local import LocalStorage
    from fashx.infrastructure.storage.s3 import S3Storage
    from .settings import get_settings

    settings = get_settings()
    if settings.storage_backend == "s3":
        return S3Storage(
            bucket=settings.s3_bucket or "fashx-media",
            endpoint_url=settings.s3_endpoint_url,
            region=settings.s3_region,
            key_id=settings.s3_access_key_id.get_secret_value() if settings.s3_access_key_id else None,
            secret=settings.s3_secret_access_key.get_secret_value() if settings.s3_secret_access_key else None,
        )
    return LocalStorage(root_dir=settings.local_storage_dir)
