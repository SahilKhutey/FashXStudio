from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from fashx.account.repository import AccountRepository
from fashx.account.schemas import (
    AccountDeletionRequest,
    AccountDeletionResponse,
    AccountDeletionStatusResponse,
    AccountDisableRequest,
    AccountDisableResponse,
    AccountMeResponse,
    AccountProvisionRequest,
    AccountProvisionResponse,
    EmailChangeConfirmRequest,
    EmailChangeConfirmResponse,
    EmailChangeRequest,
    EmailChangeResponse,
    SessionRevokeAllResponse,
)
from fashx.account.service import AccountService
from fashx.core.database import get_db_session
from fashx.core.dependencies import get_storage
from fashx.security.deps import Principal, get_principal

router = APIRouter(prefix="/account", tags=["account"])


def get_account_service(db: AsyncSession = Depends(get_db_session)) -> AccountService:
    repo = AccountRepository(db)
    return AccountService(repo)


@router.post(
    "/provision",
    response_model=AccountProvisionResponse,
    status_code=status.HTTP_200_OK,
)
async def provision_account(
    req: AccountProvisionRequest,
    principal: Principal = Depends(get_principal),
    service: AccountService = Depends(get_account_service),
) -> AccountProvisionResponse:
    preferred_id = UUID(principal.user_id) if principal.user_id else None
    return await service.provision_account(
        provider="cognito",
        provider_subject=principal.subject,
        req=req,
        preferred_user_id=preferred_id,
    )


@router.get(
    "/me",
    response_model=AccountMeResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_account(
    principal: Principal = Depends(get_principal),
    service: AccountService = Depends(get_account_service),
) -> AccountMeResponse:
    user_id = UUID(principal.user_id) if principal.user_id else None
    return await service.get_account_me(
        user_id=user_id,
        roles=sorted(principal.roles),
        subject=principal.subject,
        provider="cognito",
    )


@router.post(
    "/email-change",
    response_model=EmailChangeResponse,
    status_code=status.HTTP_200_OK,
)
async def request_email_change(
    req: EmailChangeRequest,
    principal: Principal = Depends(get_principal),
    service: AccountService = Depends(get_account_service),
) -> EmailChangeResponse:
    user_id = UUID(principal.user_id) if principal.user_id else None
    return await service.request_email_change(
        user_id=user_id,
        req=req,
        subject=principal.subject,
        provider="cognito",
    )


@router.post(
    "/email-change/confirm",
    response_model=EmailChangeConfirmResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_email_change(
    req: EmailChangeConfirmRequest,
    principal: Principal = Depends(get_principal),
    service: AccountService = Depends(get_account_service),
) -> EmailChangeConfirmResponse:
    user_id = UUID(principal.user_id) if principal.user_id else None
    return await service.confirm_email_change(
        user_id=user_id,
        req=req,
        subject=principal.subject,
        provider="cognito",
    )


@router.post(
    "/disable",
    response_model=AccountDisableResponse,
    status_code=status.HTTP_200_OK,
)
async def disable_account(
    req: AccountDisableRequest,
    principal: Principal = Depends(get_principal),
    service: AccountService = Depends(get_account_service),
) -> AccountDisableResponse:
    user_id = UUID(principal.user_id) if principal.user_id else None
    return await service.disable_account(
        user_id=user_id,
        subject=principal.subject,
        req=req,
    )


@router.post(
    "/deletion-request",
    response_model=AccountDeletionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_account_deletion(
    req: AccountDeletionRequest,
    principal: Principal = Depends(get_principal),
    service: AccountService = Depends(get_account_service),
    storage: Any = Depends(get_storage),
) -> AccountDeletionResponse:
    user_id = UUID(principal.user_id) if principal.user_id else None
    return await service.request_deletion(
        user_id=user_id,
        subject=principal.subject,
        storage=storage,
    )


@router.get(
    "/deletion-status",
    response_model=AccountDeletionStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_account_deletion_status(
    principal: Principal = Depends(get_principal),
    service: AccountService = Depends(get_account_service),
) -> AccountDeletionStatusResponse:
    user_id = UUID(principal.user_id) if principal.user_id else None
    return await service.get_deletion_status(
        user_id=user_id,
        subject=principal.subject,
        provider="cognito",
    )


@router.post(
    "/sessions/revoke-all",
    response_model=SessionRevokeAllResponse,
    status_code=status.HTTP_200_OK,
)
async def revoke_all_sessions(
    principal: Principal = Depends(get_principal),
    service: AccountService = Depends(get_account_service),
) -> SessionRevokeAllResponse:
    user_id = UUID(principal.user_id) if principal.user_id else None
    return await service.revoke_all_sessions(
        user_id=user_id,
        subject=principal.subject,
    )
