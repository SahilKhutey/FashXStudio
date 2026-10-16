from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import func, select

from database.models.catalog import StyleQuizPick
from database.models.profile import OnboardingProfile
from fashx.application.erasure import erase_account
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import Principal, get_principal

router = APIRouter(tags=["me"])


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
    try:
        user_uuid = UUID(principal.user_id)
    except ValueError:
        user_uuid = UUID(int=0)

    missing: list[str] = []
    consented_version: str | None = None
    consent_version_required = "2026.1"

    async with profile_uow:
        # 1. Check consent
        consents = await profile_uow.consents.list_for_user(user_uuid)
        active_consent = next(
            (c for c in consents if c.granted and (c.policy_version == consent_version_required or c.policy_version)),
            None,
        )
        if active_consent:
            consented_version = active_consent.policy_version
        if not active_consent or active_consent.policy_version != consent_version_required:
            missing.append("consent")

        # 2. Check profile
        onboarding_prof = await profile_uow.session.get(OnboardingProfile, user_uuid)
        body_prof = await profile_uow.body_profiles.get_by_user_id(user_uuid)
        if not (onboarding_prof and onboarding_prof.status == "completed") and not body_prof:
            missing.append("profile")

        # 3. Check quiz
        quiz_count_stmt = select(func.count(StyleQuizPick.id)).where(StyleQuizPick.user_id == user_uuid)
        quiz_count = (await profile_uow.session.scalar(quiz_count_stmt)) or 0
        if quiz_count < 1:
            missing.append("quiz")

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
    try:
        user_uuid = UUID(principal.user_id)
    except ValueError:
        user_uuid = UUID(int=0)

    async with uow:
        await erase_account(uow, user_uuid, storage=storage)
        await uow.commit()

    return EraseAccountResponse(
        user_id=principal.user_id,
        status="queued",
        message="Account erasure and storage cleanup queued",
    )
