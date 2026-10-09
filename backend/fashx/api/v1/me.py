from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from fashx.application.erasure import erase_account
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import Principal, get_principal

router = APIRouter(tags=["me"])


def get_profile_uow() -> ProfileUnitOfWork:
    return ProfileUnitOfWork(get_session_factory())


class MeResponse(BaseModel):
    user_id: str
    roles: list[str]


class EraseAccountResponse(BaseModel):
    user_id: str
    status: str = "queued"
    message: str = "Account erasure and storage cleanup queued"


@router.get("/me", response_model=MeResponse)
async def get_me(principal: Principal = Depends(get_principal)) -> MeResponse:
    return MeResponse(
        user_id=principal.user_id,
        roles=sorted(principal.roles),
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
