from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from fashx.core.database import get_db_session
from fashx.core.dependencies import get_storage
from fashx.security.deps import Principal, get_principal
from fashx.security.errors import unauthorized

from .repository import MediaRepository
from .schemas import (
    MediaAccessUrlResponse,
    MediaDeletionResponse,
    MediaMetadataResponse,
    UploadCompleteRequest,
    UploadInitiateRequest,
    UploadInitiateResponse,
    UploadStatusResponse,
)
from .service import MediaUploadService

router = APIRouter(prefix="/media", tags=["media"])


async def get_media_service(
    session: AsyncSession = Depends(get_db_session),
    storage: object = Depends(get_storage),
) -> AsyncIterator[MediaUploadService]:
    repo = MediaRepository(session)
    yield MediaUploadService(repo, storage)


def _get_user_uuid(principal: Principal) -> UUID:
    try:
        return UUID(str(principal.user_id))
    except (ValueError, TypeError, AttributeError):
        raise unauthorized("Invalid principal user ID")


@router.post(
    "/uploads",
    response_model=UploadInitiateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate photo upload intent",
)
async def initiate_upload(
    req: UploadInitiateRequest,
    principal: Principal = Depends(get_principal),
    service: MediaUploadService = Depends(get_media_service),
) -> UploadInitiateResponse:
    user_id = _get_user_uuid(principal)
    return await service.initiate(user_id=user_id, payload=req)


@router.get(
    "/uploads/{upload_id}",
    response_model=UploadStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Poll photo upload validation status",
)
async def get_upload_status(
    upload_id: UUID,
    principal: Principal = Depends(get_principal),
    service: MediaUploadService = Depends(get_media_service),
) -> UploadStatusResponse:
    user_id = _get_user_uuid(principal)
    return await service.get_upload_status(user_id=user_id, upload_id=upload_id)


@router.post(
    "/uploads/{upload_id}/complete",
    response_model=UploadStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete upload and trigger validation",
)
async def complete_upload(
    upload_id: UUID,
    req: UploadCompleteRequest | None = None,
    principal: Principal = Depends(get_principal),
    service: MediaUploadService = Depends(get_media_service),
) -> UploadStatusResponse:
    user_id = _get_user_uuid(principal)
    return await service.complete(user_id=user_id, upload_id=upload_id, payload=req)


@router.get(
    "/{image_id}",
    response_model=MediaMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve validated image metadata",
)
async def get_image_metadata(
    image_id: UUID,
    principal: Principal = Depends(get_principal),
    service: MediaUploadService = Depends(get_media_service),
) -> MediaMetadataResponse:
    user_id = _get_user_uuid(principal)
    return await service.get_metadata(user_id=user_id, image_id=image_id)


@router.post(
    "/{image_id}/access-url",
    response_model=MediaAccessUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate expiring download URL for personal image",
)
async def create_access_url(
    image_id: UUID,
    principal: Principal = Depends(get_principal),
    service: MediaUploadService = Depends(get_media_service),
) -> MediaAccessUrlResponse:
    user_id = _get_user_uuid(principal)
    return await service.create_access_url(user_id=user_id, image_id=image_id)


@router.delete(
    "/{image_id}",
    response_model=MediaDeletionResponse,
    status_code=status.HTTP_200_OK,
    summary="Request deletion of user personal image",
)
async def delete_image(
    image_id: UUID,
    principal: Principal = Depends(get_principal),
    service: MediaUploadService = Depends(get_media_service),
) -> MediaDeletionResponse:
    user_id = _get_user_uuid(principal)
    return await service.delete_media(user_id=user_id, image_id=image_id)
