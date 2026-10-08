from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.auth.internal import require_internal_service
from api.app.core.dependencies import db_session, object_storage, profile_media_repository, profile_photo_job_repository, profile_photo_queue, profile_intelligence_repository
from api.app.profile.application.media_use_cases import ProfileMediaApplicationService
from api.app.profile.application.profile_use_cases import ProfileApplicationService
from api.app.profile.application.photo_job_use_cases import ProfilePhotoJobApplicationService
from api.app.profile.application.intelligence_use_cases import ProfileIntelligenceApplicationService
from api.app.profile.repositories.media import ProfileMediaRepository
from api.app.profile.repositories.profile import ProfileRepository
from api.app.profile.repositories.media_jobs import ProfilePhotoJobRepository
from api.app.ports.queue import QueuePort
from api.app.ports.storage import ObjectStoragePort
from schemas.identity.consent import ConsentRecord, ConsentUpdate
from schemas.identity.media import (
    MediaAccessRequest,
    MediaAccessResponse,
    PhotoCompleteResponse,
    PhotoCreateRequest,
    PhotoCreateResponse,
    PhotoStatusResponse,
    PhotoGuidanceResponse,
)
from schemas.identity.user import UserRef
from schemas.profile.profile_photo_job import PhotoJobClaimResponse, PhotoJobCompleteRequest, PhotoJobFailureResponse, PhotoJobFailRequest
from schemas.profile.body import BodyProfile
from schemas.profile.derived import DerivedProfile
from schemas.profile.intelligence import ProfileReadiness, ProfileArtifactResponse, SkinToneResult
from schemas.profile.profile import ProfileCreateRequest, ProfileResponse
from schemas.profile.preferences import UserPreferences

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


def get_service(session: AsyncSession = Depends(db_session)) -> ProfileApplicationService:
    return ProfileApplicationService(ProfileRepository(session))


def get_media_service(
    repository: ProfileMediaRepository = Depends(profile_media_repository),
    storage: ObjectStoragePort = Depends(object_storage),
    queue: QueuePort = Depends(profile_photo_queue),
) -> ProfileMediaApplicationService:
    return ProfileMediaApplicationService(repository, storage, queue)


def get_photo_job_service(
    repository: ProfilePhotoJobRepository = Depends(profile_photo_job_repository),
    queue: QueuePort = Depends(profile_photo_queue),
) -> ProfilePhotoJobApplicationService:
    return ProfilePhotoJobApplicationService(repository, queue)



def get_intelligence_service(repository=Depends(profile_intelligence_repository)) -> ProfileIntelligenceApplicationService:
    return ProfileIntelligenceApplicationService(repository)

@router.post("", response_model=UserRef, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: ProfileCreateRequest,
    user_id=Depends(current_user_id),
    service: ProfileApplicationService = Depends(get_service),
    intelligence: ProfileIntelligenceApplicationService = Depends(get_intelligence_service),
) -> UserRef:
    await service.update_profile(
        user_id,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        build=payload.build,
        colors_favored=payload.colors_favored,
        colors_avoided=payload.colors_avoided,
        categories=payload.categories,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
    )
    await intelligence.snapshot(user_id)
    return UserRef(user_id=user_id)


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user_id=Depends(current_user_id),
    service: ProfileApplicationService = Depends(get_service),
) -> ProfileResponse:
    user, body, preferences = await service.get_profile(user_id)
    return ProfileResponse(
        user_id=user.id,
        created_at=user.created_at,
        body=BodyProfile.model_validate(body, from_attributes=True) if body else BodyProfile(),
        preferences=UserPreferences.model_validate(preferences, from_attributes=True) if preferences else UserPreferences(),
    )


@router.get("/{user_id}/derived", response_model=DerivedProfile)
async def get_derived_profile(
    user_id,
    requester_id=Depends(current_user_id),
    service: ProfileApplicationService = Depends(get_service),
    intelligence: ProfileIntelligenceApplicationService = Depends(get_intelligence_service),
) -> DerivedProfile:
    if requester_id != user_id:
        from api.app.core.errors import AuthorizationError
        raise AuthorizationError("Derived profile access denied")
    _body, preferences, style = await service.get_derived(user_id)
    style_vector = list(style.embedding) if style and style.embedding else None
    data = await intelligence.derived(
        user_id,
        style_vector=style_vector,
        preferences={
            "colors_favored": getattr(preferences, "colors_favored", []),
            "colors_avoided": getattr(preferences, "colors_avoided", []),
            "categories": getattr(preferences, "categories", []),
            "budget_min": getattr(preferences, "budget_min", None),
            "budget_max": getattr(preferences, "budget_max", None),
        },
    )
    return DerivedProfile.model_validate(data)


@router.get("/me/readiness", response_model=ProfileReadiness)
async def get_profile_readiness(
    user_id=Depends(current_user_id),
    intelligence: ProfileIntelligenceApplicationService = Depends(get_intelligence_service),
) -> ProfileReadiness:
    return ProfileReadiness.model_validate(await intelligence.readiness(user_id))


@router.get("/me/artifacts/latest", response_model=ProfileArtifactResponse)
async def get_latest_profile_artifact(
    user_id=Depends(current_user_id),
    intelligence: ProfileIntelligenceApplicationService = Depends(get_intelligence_service),
) -> ProfileArtifactResponse:
    artifact = await intelligence.repository.latest_artifact(user_id)
    if artifact is None:
        from api.app.core.errors import NotFoundError
        raise NotFoundError("Profile artifact not found")
    skin = await intelligence.repository.latest_skin_tone(user_id)
    return ProfileArtifactResponse(
        artifact_id=artifact.id, user_id=artifact.user_id, version=artifact.version,
        body=artifact.body_snapshot, preferences=artifact.preferences_snapshot,
        tryon_photo_id=artifact.tryon_photo_id,
        skin_tone=SkinToneResult.model_validate(skin, from_attributes=True) if skin else None,
        ready_for_tryon=artifact.ready_for_tryon, created_at=artifact.created_at,
    )


@router.post("/consent", response_model=ConsentRecord)
async def set_consent(
    payload: ConsentUpdate,
    user_id=Depends(current_user_id),
    service: ProfileMediaApplicationService = Depends(get_media_service),
) -> ConsentRecord:
    record = await service.set_consent(user_id, data_type=payload.data_type, granted=payload.granted)
    return ConsentRecord(user_id=user_id, data_type=payload.data_type, granted=record.granted, updated_at=record.updated_at)


@router.post("/me/photos", response_model=PhotoCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_photo_upload(
    payload: PhotoCreateRequest,
    user_id=Depends(current_user_id),
    service: ProfileMediaApplicationService = Depends(get_media_service),
) -> PhotoCreateResponse:
    photo, upload_url, expires_at = await service.create_photo_upload(
        user_id,
        photo_type=payload.photo_type,
        content_type=payload.content_type,
        file_size_bytes=payload.file_size_bytes,
    )
    return PhotoCreateResponse(
        photo_id=photo.id,
        status=photo.status,
        upload_url=upload_url,
        expires_at=expires_at,
    )


@router.post("/me/photos/{photo_id}/complete", response_model=PhotoCompleteResponse, status_code=status.HTTP_202_ACCEPTED)
async def complete_photo_upload(
    photo_id,
    user_id=Depends(current_user_id),
    service: ProfileMediaApplicationService = Depends(get_media_service),
) -> PhotoCompleteResponse:
    photo, job = await service.complete_photo_upload(user_id, photo_id)
    return PhotoCompleteResponse(photo_id=photo.id, status=photo.status, processing_job_id=job.id)


@router.get("/me/photos/{photo_id}", response_model=PhotoStatusResponse)
async def get_photo_status(
    photo_id,
    user_id=Depends(current_user_id),
    service: ProfileMediaApplicationService = Depends(get_media_service),
) -> PhotoStatusResponse:
    photo = await service.get_photo_status(user_id, photo_id)
    return PhotoStatusResponse(
        photo_id=photo.id,
        photo_type=photo.photo_type,
        status=photo.status,
        reject_reason=photo.reject_reason,
        version=photo.version,
        created_at=photo.created_at,
        quality_score=photo.quality_score,
        pose_score=photo.pose_score,
        framing_score=photo.framing_score,
        landmark_confidence=photo.landmark_confidence,
        ready_for_tryon=photo.ready_for_tryon,
        quality_reasons=photo.quality_reasons or [],
        pose_provider=photo.pose_provider,
        pose_provider_version=photo.pose_provider_version,
    )


@router.get("/me/photos/{photo_id}/guidance", response_model=PhotoGuidanceResponse)
async def get_photo_guidance(
    photo_id,
    user_id=Depends(current_user_id),
    service: ProfileMediaApplicationService = Depends(get_media_service),
) -> PhotoGuidanceResponse:
    return PhotoGuidanceResponse.model_validate(await service.get_capture_guidance(user_id, photo_id))


@router.post("/internal/skin-tone-jobs/{job_id}/complete", response_model=dict, dependencies=[Depends(require_internal_service)])
async def complete_skin_tone_job(
    job_id,
    payload: dict,
    intelligence: ProfileIntelligenceApplicationService = Depends(get_intelligence_service),
) -> dict:
    from api.app.core.errors import NotFoundError
    from api.app.core.transactions import transaction
    from database.models.identity import ProfilePhotoJob
    async with transaction(intelligence.repository.session):
        job = await intelligence.repository.session.get(ProfilePhotoJob, job_id)
        if job is None:
            raise NotFoundError("Profile photo job not found")
        result = await intelligence.repository.upsert_skin_tone(
            user_id=job.user_id, photo_id=job.photo_id, ita_degrees=payload.get("ita_degrees"),
            tone_class=payload.get("tone_class"), confidence=float(payload.get("confidence", 0.0)),
            method=str(payload.get("method", "ita_face_crop_v1")), model_version=str(payload.get("model_version", "1.0")),
            status=str(payload.get("status", "completed")),
        )
    artifact, _skin = await intelligence.snapshot(job.user_id)
    return {"status": result.status, "result_id": str(result.id), "photo_id": str(result.photo_id), "artifact_id": str(artifact.id)}


@router.post("/internal/media-access", response_model=MediaAccessResponse, dependencies=[Depends(require_internal_service)])
async def create_scoped_media_access(
    payload: MediaAccessRequest,
    service: ProfileMediaApplicationService = Depends(get_media_service),
) -> MediaAccessResponse:
    access_url, expires_at = await service.create_scoped_media_url(
        photo_id=payload.photo_id,
        purpose=payload.purpose,
        job_id=payload.job_id,
    )
    return MediaAccessResponse(
        photo_id=payload.photo_id,
        access_url=access_url,
        expires_at=expires_at,
        purpose=payload.purpose,
        job_id=payload.job_id,
    )


@router.post("/internal/photo-jobs/{job_id}/claim", response_model=PhotoJobClaimResponse)
async def claim_photo_job(
    job_id,
    _: None = Depends(require_internal_service),
    service: ProfilePhotoJobApplicationService = Depends(get_photo_job_service),
) -> PhotoJobClaimResponse:
    return PhotoJobClaimResponse.model_validate(await service.claim(job_id))


@router.post("/internal/photo-jobs/{job_id}/complete", response_model=dict)
async def complete_photo_job(
    job_id,
    payload: PhotoJobCompleteRequest,
    _: None = Depends(require_internal_service),
    service: ProfilePhotoJobApplicationService = Depends(get_photo_job_service),
) -> dict:
    return await service.complete(job_id, payload.model_dump())


@router.post("/internal/photo-jobs/{job_id}/fail", response_model=PhotoJobFailureResponse)
async def fail_photo_job(
    job_id,
    payload: PhotoJobFailRequest,
    _: None = Depends(require_internal_service),
    service: ProfilePhotoJobApplicationService = Depends(get_photo_job_service),
) -> PhotoJobFailureResponse:
    return PhotoJobFailureResponse.model_validate(
        await service.fail(job_id, reason=payload.reason, retryable=payload.retryable)
    )
