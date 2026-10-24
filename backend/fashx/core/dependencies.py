from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from fashx.application.ports.storage import ObjectStorage
    from fashx.application.ports.tryon import TryOnAdapter
    from fashx.catalog.repositories.catalog import CatalogRepository
    from fashx.profile.repositories.profile import ProfileRepository

from .database import get_db_session


async def db_session(session: AsyncSession = Depends(get_db_session)) -> AsyncIterator[AsyncSession]:
    yield session


def profile_repository(session: AsyncSession = Depends(get_db_session)) -> ProfileRepository:
    from fashx.profile.repositories.profile import ProfileRepository

    return ProfileRepository(session)


def catalog_repository(session: AsyncSession = Depends(get_db_session)) -> CatalogRepository:
    from fashx.catalog.repositories.catalog import CatalogRepository

    return CatalogRepository(session)


def get_storage() -> ObjectStorage:
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


def get_tryon_adapter() -> TryOnAdapter:
    from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter
    from fashx.ml.licenses import assert_production_license
    from fashx.tryon.adapters.mock_adapter import MockAdapter

    from .settings import get_settings

    s = get_settings()
    if s.tryon_provider == "fashn_api":
        if not s.fashn_api_key or not s.fashn_api_key.get_secret_value():
            raise ValueError("FASHN_API_KEY required when TRYON_PROVIDER=fashn_api")
        adapter = FashnApiAdapter(
            api_key=s.fashn_api_key.get_secret_value(),
            base_url=s.fashn_base_url,
            model=s.fashn_model,
            mode=s.fashn_mode,
            cost_usd_est=s.tryon_est_cost_usd,
        )
    else:
        adapter = MockAdapter()

    if s.env == "prod":
        assert_production_license(adapter)

    return adapter
