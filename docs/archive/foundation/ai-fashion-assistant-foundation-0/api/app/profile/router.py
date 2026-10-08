from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.dependencies import current_user_id
from api.app.core.dependencies import db_session
from api.app.profile.application.profile_use_cases import ProfileApplicationService
from api.app.profile.repositories.profile import ProfileRepository
from schemas.identity.user import UserRef
from schemas.profile.derived import DerivedProfile
from schemas.profile.profile import ProfileCreateRequest, ProfileResponse
from schemas.profile.body import BodyProfile
from schemas.profile.preferences import UserPreferences

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


def get_service(session: AsyncSession = Depends(db_session)) -> ProfileApplicationService:
    return ProfileApplicationService(ProfileRepository(session))


@router.post("", response_model=UserRef, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: ProfileCreateRequest,
    user_id = Depends(current_user_id),
    service: ProfileApplicationService = Depends(get_service),
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
    return UserRef(user_id=user_id)


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user_id = Depends(current_user_id),
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
    requester_id = Depends(current_user_id),
    service: ProfileApplicationService = Depends(get_service),
) -> DerivedProfile:
    # Cross-service consumers are expected to use internal auth in later stages. Foundation 3
    # keeps this route restricted to self-access until the service-to-service identity layer exists.
    if requester_id != user_id:
        from api.app.core.errors import AuthorizationError
        raise AuthorizationError("Derived profile access denied")
    body, preferences, style = await service.get_derived(user_id)
    style_vector = list(style.embedding) if style and style.embedding else None
    return DerivedProfile(
        skin_tone_class=None,
        style_vector=style_vector,
        preferences={
            "colors_favored": getattr(preferences, "colors_favored", []),
            "colors_avoided": getattr(preferences, "colors_avoided", []),
            "categories": getattr(preferences, "categories", []),
            "budget_min": getattr(preferences, "budget_min", None),
            "budget_max": getattr(preferences, "budget_max", None),
        },
    )
