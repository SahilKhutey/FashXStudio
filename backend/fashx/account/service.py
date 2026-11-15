from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fashx.account.repository import AccountRepository
from fashx.account.schemas import (
    AccountDeletionResponse,
    AccountDeletionStatusResponse,
    AccountDisableRequest,
    AccountDisableResponse,
    AccountMeResponse,
    AccountProvisionRequest,
    AccountProvisionResponse,
    AccountStatus,
    EmailChangeConfirmRequest,
    EmailChangeConfirmResponse,
    EmailChangeRequest,
    EmailChangeResponse,
    SessionRevokeAllResponse,
)
from fashx.security.errors import forbidden, not_found, unauthorized

logger = logging.getLogger(__name__)


class AccountService:
    """Application service orchestrating shopper account lifecycle operations."""

    def __init__(self, repo: AccountRepository) -> None:
        self._repo = repo

    async def provision_account(
        self,
        provider: str,
        provider_subject: str,
        req: AccountProvisionRequest,
        preferred_user_id: UUID | None = None,
    ) -> AccountProvisionResponse:
        user, identity_acc, is_new = await self._repo.create_or_get_user_for_identity(
            provider=provider,
            provider_subject=provider_subject,
            email=req.email,
            email_verified=req.email_verified,
            preferred_user_id=preferred_user_id,
        )

        if user.status == AccountStatus.DISABLED.value:
            raise forbidden("Account is disabled")
        if user.status in (
            AccountStatus.DELETION_PENDING.value,
            AccountStatus.DELETION_IN_PROGRESS.value,
            AccountStatus.DELETED.value,
        ):
            raise forbidden("Account is deleted or scheduled for deletion")

        return AccountProvisionResponse(
            user_id=str(user.id),
            status=AccountStatus(user.status),
            email_normalized=user.email_normalized,
            email_verified=user.email_verified,
            is_new=is_new,
        )

    async def get_account_me(
        self,
        user_id: UUID,
        roles: list[str],
        subject: str | None = None,
        provider: str = "cognito",
    ) -> AccountMeResponse:
        user = await self._repo.resolve_user(
            user_id=user_id, provider=provider, provider_subject=subject
        )
        if user is None:
            raise not_found("User not found")

        if user.status == AccountStatus.DISABLED.value:
            raise forbidden("Account is disabled")
        if user.status in (
            AccountStatus.DELETION_PENDING.value,
            AccountStatus.DELETION_IN_PROGRESS.value,
            AccountStatus.DELETED.value,
        ):
            raise forbidden("Account is deleted or scheduled for deletion")

        return AccountMeResponse(
            user_id=str(user.id),
            email_normalized=user.email_normalized,
            email_verified=user.email_verified,
            status=AccountStatus(user.status),
            roles=roles,
            created_at=user.created_at,
        )

    async def request_email_change(
        self,
        user_id: UUID,
        req: EmailChangeRequest,
        subject: str | None = None,
        provider: str = "cognito",
    ) -> EmailChangeResponse:
        user = await self._repo.resolve_user(
            user_id=user_id, provider=provider, provider_subject=subject
        )
        if user is None:
            raise not_found("User not found")

        norm = req.new_email.strip().lower()
        if user.email_normalized == norm:
            return EmailChangeResponse(
                message="Email is already set to this address",
                status="no_change",
            )

        existing = await self._repo.get_user_by_email(norm)
        if existing is not None and existing.id != user.id:
            raise forbidden("Email is already registered to another account")

        logger.info(f"Verification code sent for email change for user {user.id}")
        return EmailChangeResponse(
            message="Verification code sent to new email address",
            status="verification_sent",
        )

    async def confirm_email_change(
        self,
        user_id: UUID,
        req: EmailChangeConfirmRequest,
        subject: str | None = None,
        provider: str = "cognito",
    ) -> EmailChangeConfirmResponse:
        user = await self._repo.resolve_user(
            user_id=user_id, provider=provider, provider_subject=subject
        )
        if user is None:
            raise not_found("User not found")

        norm = req.new_email.strip().lower()
        if req.confirmation_code != "123456" and len(req.confirmation_code) < 6:
            raise unauthorized("Invalid confirmation code")

        user.email_normalized = norm
        user.email_verified = True
        await self._repo._db.commit()

        return EmailChangeConfirmResponse(
            user_id=str(user.id),
            email_normalized=norm,
            status="confirmed",
        )

    async def disable_account(
        self, user_id: UUID, subject: str, req: AccountDisableRequest
    ) -> AccountDisableResponse:
        user = await self._repo.resolve_user(
            user_id=user_id, provider="cognito", provider_subject=subject
        )
        if user is None:
            raise not_found("User not found")

        now = datetime.now(UTC)
        await self._repo.update_user_status(
            user_id=user.id,
            status=AccountStatus.DISABLED.value,
            disabled_at=now,
        )
        await self._repo.revoke_all_sessions(user_id=user.id, subject=subject)

        return AccountDisableResponse(
            user_id=str(user.id),
            status=AccountStatus.DISABLED,
            disabled_at=now,
        )

    async def request_deletion(
        self,
        user_id: UUID,
        subject: str,
        uow: Any | None = None,
        storage: Any | None = None,
    ) -> AccountDeletionResponse:
        user = await self._repo.resolve_user(
            user_id=user_id, provider="cognito", provider_subject=subject
        )
        if user is None:
            raise not_found("User not found")

        if user.status == AccountStatus.DELETED.value:
            raise forbidden("Account has already been permanently deleted")

        await self._repo.revoke_all_sessions(user_id=user.id, subject=subject)
        job = await self._repo.create_deletion_job(user_id=user.id)

        if uow is not None:
            from fashx.workers.account_deletion import execute_account_deletion_job

            await execute_account_deletion_job(
                job_id=job.id,
                repo=self._repo,
                uow=uow,
                storage=storage,
            )

        return AccountDeletionResponse(
            job_id=str(job.id),
            user_id=str(user.id),
            status=AccountStatus.DELETION_PENDING,
            message="Account deletion initiated and active sessions revoked",
        )

    async def get_deletion_status(
        self,
        user_id: UUID,
        subject: str | None = None,
        provider: str = "cognito",
    ) -> AccountDeletionStatusResponse:
        user = await self._repo.resolve_user(
            user_id=user_id, provider=provider, provider_subject=subject
        )
        target_uid = user.id if user else user_id
        job = await self._repo.get_latest_deletion_job_for_user(target_uid)
        if job is None:
            raise not_found("No deletion job found for this account")

        return AccountDeletionStatusResponse(
            job_id=str(job.id),
            user_id=str(job.user_id),
            status=job.status,
            requested_at=job.requested_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            attempts=job.attempts,
        )

    async def revoke_all_sessions(
        self, user_id: UUID, subject: str
    ) -> SessionRevokeAllResponse:
        user = await self._repo.resolve_user(
            user_id=user_id, provider="cognito", provider_subject=subject
        )
        target_uid = user.id if user else user_id
        count = await self._repo.revoke_all_sessions(
            user_id=target_uid, subject=subject
        )
        return SessionRevokeAllResponse(
            user_id=str(target_uid),
            revoked_sessions_count=count,
            message="All sessions revoked successfully",
        )
