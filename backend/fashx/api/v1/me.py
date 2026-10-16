from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import func, select

from database.models.catalog import StyleQuizPick
from database.models.identity import UserPhoto
from database.models.profile import OnboardingProfile
from fashx.api.v1.onboarding import MIN_QUIZ_PICKS
from fashx.application.erasure import erase_account
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.core.settings import get_settings
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import Principal, get_principal

logger = logging.getLogger(__name__)

router = APIRouter(tags=["me"])

REQUIRED_CONSENTS = ("terms_and_privacy", "body_photo")


def consent_ok(consents: list[Any], version: str) -> bool:
    granted = {c.data_type for c in consents if c.granted and c.consent_version == version}
    return all(t in granted for t in REQUIRED_CONSENTS)


def get_profile_uow() -> ProfileUnitOfWork:
    return ProfileUnitOfWork(get_session_factory())


class OnboardingStatus(BaseModel):
    complete: bool
    missing: list[str] = []
    consent_version_required: str = "2026.1"
    consented_version: str | None = None


class MeResponse(BaseModel):
    user_id: str
    roles: list[str]
    onboarding: OnboardingStatus


class EraseAccountResponse(BaseModel):
    user_id: str
    status: str = "queued"
    message: str = "Account erasure and storage cleanup queued"


@router.get("/me", response_model=MeResponse)
async def get_me(
    principal: Principal = Depends(get_principal),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> MeResponse:
    user_uuid = UUID(principal.user_id)

    missing: list[str] = []
    consented_version: str | None = None
    consent_version_required = get_settings().consent_version

    async with profile_uow:
        # 1. Check consent
        consents = await profile_uow.consents.list_for_user(user_uuid)
        if consent_ok(consents, consent_version_required):
            consented_version = consent_version_required
        else:
            missing.append("consent")

        # 2. Check profile
        onboarding_prof = await profile_uow.session.get(OnboardingProfile, user_uuid)
        body_prof = await profile_uow.body_profiles.get_by_user_id(user_uuid)
        if not (onboarding_prof and onboarding_prof.status == "completed") and not body_prof:
            missing.append("profile")

        # 3. Check style_quiz
        quiz_count_stmt = select(func.count(StyleQuizPick.id)).where(
            StyleQuizPick.user_id == user_uuid
        )
        quiz_count = (await profile_uow.session.scalar(quiz_count_stmt)) or 0
        if quiz_count < MIN_QUIZ_PICKS:
            missing.append("style_quiz")

        # 4. Check photo
        photo_count_stmt = select(func.count(UserPhoto.id)).where(
            UserPhoto.user_id == user_uuid, UserPhoto.status == "accepted"
        )
        photo_count = (await profile_uow.session.scalar(photo_count_stmt)) or 0
        if photo_count < 1:
            missing.append("photo")

    return MeResponse(
        user_id=principal.user_id,
        roles=sorted(principal.roles),
        onboarding=OnboardingStatus(
            complete=len(missing) == 0,
            missing=missing,
            consent_version_required=consent_version_required,
            consented_version=consented_version,
        ),
    )


@router.delete("/me", status_code=status.HTTP_202_ACCEPTED, response_model=EraseAccountResponse)
async def delete_me(
    principal: Principal = Depends(get_principal),
    storage: Any = Depends(get_storage),
    uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> EraseAccountResponse:
    from fashx.application.erasure import ErasureIncomplete
    from fashx.security.errors import ApiError

    user_uuid = UUID(principal.user_id)

    try:
        async with uow:
            await erase_account(uow, user_uuid, storage=storage)
    except ErasureIncomplete:
        logger.exception(f"Account erasure incomplete for user {user_uuid}")
        raise ApiError(
            status=503,
            code="erasure_incomplete",
            detail="Account deletion is still in progress. Please try again.",
        )

    return EraseAccountResponse(
        user_id=principal.user_id,
        status="queued",
        message="Account erasure and storage cleanup queued",
    )
