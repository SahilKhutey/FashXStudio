from __future__ import annotations

import logging
from datetime import datetime
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


class MeConsentItem(BaseModel):
    user_id: UUID
    data_type: str
    granted: bool
    consent_version: str
    is_18_or_older: bool | None = None
    consented_at: datetime
    updated_at: datetime


class UpdateConsentBody(BaseModel):
    granted: bool
    consent_version: str | None = None
    is_18_or_older: bool | None = None
    policy_url: str | None = None


@router.get("/me/consents", response_model=list[MeConsentItem])
async def get_my_consents(
    principal: Principal = Depends(get_principal),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> list[MeConsentItem]:
    user_uuid = UUID(principal.user_id)
    async with profile_uow:
        consents = await profile_uow.consents.list_for_user(user_uuid)
        return [
            MeConsentItem(
                user_id=c.user_id,
                data_type=c.data_type,
                granted=c.granted,
                consent_version=c.consent_version,
                is_18_or_older=c.is_18_or_older,
                consented_at=c.consented_at,
                updated_at=c.updated_at,
            )
            for c in consents
        ]


@router.put("/me/consents/{data_type}", response_model=MeConsentItem)
async def update_my_consent_alias(
    data_type: str,
    req: UpdateConsentBody,
    principal: Principal = Depends(get_principal),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
) -> MeConsentItem:
    user_uuid = UUID(principal.user_id)
    version = req.consent_version or get_settings().consent_version
    async with profile_uow:
        rec = await profile_uow.consents.upsert(
            user_id=user_uuid,
            data_type=data_type,
            granted=req.granted,
            is_18_or_older=req.is_18_or_older,
            consent_version=version,
            decision_source="me_api",
            policy_url=req.policy_url,
        )
        await profile_uow.commit()

        return MeConsentItem(
            user_id=rec.user_id,
            data_type=rec.data_type,
            granted=rec.granted,
            consent_version=rec.consent_version,
            is_18_or_older=rec.is_18_or_older,
            consented_at=rec.consented_at,
            updated_at=rec.updated_at,
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
