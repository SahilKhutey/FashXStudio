import base64
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from schemas.common.enums import BuildType, MeasurementSource, PhotoType
from schemas.identity.consent import ConsentUpdate

from fashx.core.database import get_session_factory
from fashx.core.errors import EntityNotFoundError, ValidationError
from fashx.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from fashx.profile.application.record_measurement import (
    RecordMeasurementCommand,
    RecordMeasurementUseCase,
)
from fashx.profile.application.update_preferences import (
    UpdatePreferencesCommand,
    UpdatePreferencesUseCase,
)
from fashx.profile.application.upload_photo import (
    UploadPhotoCommand,
    UploadUserPhotoUseCase,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork

router = APIRouter(prefix="/profile", tags=["profile"])


def get_profile_uow() -> ProfileUnitOfWork:
    return ProfileUnitOfWork(get_session_factory())


class CreateProfileRequest(BaseModel):
    height_cm: int | None = Field(default=None, ge=100, le=250)
    weight_kg: int | None = Field(default=None, ge=25, le=300)
    build: BuildType | None = None
    consents: list[ConsentUpdate] = []


class CreateProfileResponse(BaseModel):
    user_id: UUID
    height_cm: int | None = None
    weight_kg: int | None = None
    build: str | None = None
    consents: dict[str, bool] = {}


class RecordMeasurementRequest(BaseModel):
    user_id: UUID
    measurement: str
    value: float = Field(gt=0)
    unit: str
    source: MeasurementSource = MeasurementSource.USER_ENTERED
    confidence: float | None = Field(default=None, ge=0, le=1)


class MeasurementResponse(BaseModel):
    id: UUID
    user_id: UUID
    measurement: str
    value: float
    unit: str
    source: str
    confidence: float | None = None


class UploadPhotoRequest(BaseModel):
    photo_type: PhotoType = PhotoType.TRYON_REFERENCE
    photo_b64: str


class UploadPhotoResponse(BaseModel):
    photo_id: UUID
    user_id: UUID
    photo_type: str
    status: str
    storage_key: str | None = None
    reject_reason: str | None = None
    skin_tone: dict[str, Any] | None = None


class UpdatePreferencesRequest(BaseModel):
    colors_favored: list[str] = []
    colors_avoided: list[str] = []
    categories: list[str] = []
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)


class UpdatePreferencesResponse(BaseModel):
    user_id: UUID
    colors_favored: list[str] = []
    colors_avoided: list[str] = []
    categories: list[str] = []
    budget_min: int | None = None
    budget_max: int | None = None


class UserPhotoItem(BaseModel):
    id: UUID
    photo_type: str
    status: str
    storage_key: str
    reject_reason: str | None = None


class DerivedProfileResponse(BaseModel):
    user_id: UUID
    height_cm: int | None = None
    weight_kg: int | None = None
    build: str | None = None
    consents: dict[str, bool] = {}
    measurements: list[MeasurementResponse] = []
    preferences: UpdatePreferencesResponse | None = None
    photos: list[UserPhotoItem] = []


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=CreateProfileResponse)
async def create_user_profile(
    req: CreateProfileRequest,
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> CreateProfileResponse:
    use_case = CreateProfileUseCase(uow)
    cmd = CreateProfileCommand(
        height_cm=req.height_cm,
        weight_kg=req.weight_kg,
        build=req.build.value if req.build else None,
        consents=req.consents,
    )
    res = await use_case.execute(cmd)
    return CreateProfileResponse(
        user_id=res.user_id,
        height_cm=res.height_cm,
        weight_kg=res.weight_kg,
        build=res.build,
        consents=res.consents,
    )


@router.post(
    "/measurements", status_code=status.HTTP_201_CREATED, response_model=MeasurementResponse
)
async def record_measurement(
    req: RecordMeasurementRequest,
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> MeasurementResponse:
    use_case = RecordMeasurementUseCase(uow)
    cmd = RecordMeasurementCommand(
        user_id=req.user_id,
        measurement=req.measurement,
        value=req.value,
        unit=req.unit,
        source=req.source,
        confidence=req.confidence,
    )
    measurement = await use_case.execute(cmd)
    return MeasurementResponse(
        id=measurement.id,
        user_id=measurement.user_id,
        measurement=measurement.measurement,
        value=measurement.value,
        unit=measurement.unit,
        source=measurement.source,
        confidence=measurement.confidence,
    )


@router.post(
    "/{user_id}/photos", status_code=status.HTTP_201_CREATED, response_model=UploadPhotoResponse
)
async def upload_user_photo(
    user_id: UUID,
    req: UploadPhotoRequest,
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> UploadPhotoResponse:
    try:
        raw_bytes = base64.b64decode(req.photo_b64)
    except Exception:
        raise ValidationError("Invalid base64 encoded photo payload", field="photo_b64") from None

    use_case = UploadUserPhotoUseCase(uow)
    cmd = UploadPhotoCommand(
        user_id=user_id,
        photo_type=req.photo_type,
        photo_bytes=raw_bytes,
    )
    res = await use_case.execute(cmd)
    skin_tone_dict = None
    if res.skin_tone:
        skin_tone_dict = {
            "monk_scale_index": res.skin_tone.monk_scale_index,
            "hex_code": res.skin_tone.hex_code,
            "undertone": res.skin_tone.undertone,
            "rgb": res.skin_tone.rgb,
        }

    return UploadPhotoResponse(
        photo_id=res.photo_id,
        user_id=res.user_id,
        photo_type=res.photo_type,
        status=res.status,
        storage_key=res.storage_key,
        reject_reason=res.reject_reason,
        skin_tone=skin_tone_dict,
    )


@router.put("/{user_id}/preferences", response_model=UpdatePreferencesResponse)
async def update_preferences(
    user_id: UUID,
    req: UpdatePreferencesRequest,
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> UpdatePreferencesResponse:
    use_case = UpdatePreferencesUseCase(uow)
    cmd = UpdatePreferencesCommand(
        user_id=user_id,
        colors_favored=req.colors_favored,
        colors_avoided=req.colors_avoided,
        categories=req.categories,
        budget_min=req.budget_min,
        budget_max=req.budget_max,
    )
    pref = await use_case.execute(cmd)
    return UpdatePreferencesResponse(
        user_id=pref.user_id,
        colors_favored=pref.colors_favored,
        colors_avoided=pref.colors_avoided,
        categories=pref.categories,
        budget_min=pref.budget_min,
        budget_max=pref.budget_max,
    )


@router.get("/{user_id}/derived", response_model=DerivedProfileResponse)
async def get_derived_profile(
    user_id: UUID,
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> DerivedProfileResponse:
    async with uow:
        user = await uow.users.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", user_id)

        body = await uow.body_profiles.get_by_user_id(user_id)
        consents_list = await uow.consents.list_for_user(user_id)
        measurements_list = await uow.measurements.list_by_user_id(user_id)
        pref = await uow.preferences.get_by_user_id(user_id)
        photos_list = await uow.photos.list_for_user(user_id)

        pref_response = None
        if pref:
            pref_response = UpdatePreferencesResponse(
                user_id=pref.user_id,
                colors_favored=pref.colors_favored,
                colors_avoided=pref.colors_avoided,
                categories=pref.categories,
                budget_min=pref.budget_min,
                budget_max=pref.budget_max,
            )

        return DerivedProfileResponse(
            user_id=user.id,
            height_cm=body.height_cm if body else None,
            weight_kg=body.weight_kg if body else None,
            build=body.build if body else None,
            consents={c.data_type: c.granted for c in consents_list},
            measurements=[
                MeasurementResponse(
                    id=m.id,
                    user_id=m.user_id,
                    measurement=m.measurement,
                    value=m.value,
                    unit=m.unit,
                    source=m.source,
                    confidence=m.confidence,
                )
                for m in measurements_list
            ],
            preferences=pref_response,
            photos=[
                UserPhotoItem(
                    id=p.id,
                    photo_type=p.photo_type,
                    status=p.status,
                    storage_key=p.storage_key,
                    reject_reason=p.reject_reason,
                )
                for p in photos_list
            ],
        )


class RevokeConsentRequest(BaseModel):
    data_type: str = "body_photo"


class RevokeConsentResponse(BaseModel):
    user_id: UUID
    data_type: str
    status: str
    photos_purged: int
    jobs_purged: int


@router.post(
    "/{user_id}/consent/revoke",
    response_model=RevokeConsentResponse,
    status_code=status.HTTP_200_OK,
)
async def revoke_user_consent(
    user_id: UUID,
    req: RevokeConsentRequest,
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> RevokeConsentResponse:
    """Rule I16 & Gate G4: Instantly cascades deletion of photos and tryon renders upon consent revocation."""
    from fashx.profile.application.revoke_consent import (
        RevokeConsentCommand,
        RevokeConsentUseCase,
    )
    from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork

    tryon_uow = TryOnUnitOfWork(get_session_factory())
    use_case = RevokeConsentUseCase(profile_uow, tryon_uow)
    res = await use_case.execute(RevokeConsentCommand(user_id=user_id, data_type=req.data_type))
    return RevokeConsentResponse(
        user_id=res.user_id,
        data_type=res.data_type,
        status=res.status,
        photos_purged=res.photos_purged,
        jobs_purged=res.jobs_purged,
    )
