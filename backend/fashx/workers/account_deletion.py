from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import update

from database.models.account import AccountDeletionJob
from fashx.account.repository import AccountRepository
from fashx.account.schemas import AccountStatus
from fashx.application.erasure import erase_account

logger = logging.getLogger(__name__)


async def execute_account_deletion_job(
    job_id: UUID,
    repo: AccountRepository,
    uow: Any,
    storage: Any | None = None,
    cognito_client: Any | None = None,
) -> dict[str, Any]:
    """Durable worker execution for account deletion and data erasure."""
    job = await repo.get_deletion_job(job_id)
    if job is None:
        logger.error(f"Deletion job {job_id} not found")
        return {"status": "error", "error": "Job not found"}

    if job.status == "COMPLETED":
        return {"status": "already_completed", "job_id": str(job_id)}

    user_id = job.user_id
    now = datetime.now(UTC)

    # Transition to RUNNING and DELETION_IN_PROGRESS
    job.status = "RUNNING"
    job.started_at = now
    await repo.update_user_status(
        user_id=user_id,
        status=AccountStatus.DELETION_IN_PROGRESS.value,
    )
    await repo._db.commit()

    try:
        # 1. Execute full cascade erasure of biometrics, profile, wardrobe, and S3
        if hasattr(uow, "__aenter__"):
            async with uow:
                erasure_res = await erase_account(uow, user_id, storage=storage)
        else:
            erasure_res = await erase_account(uow, user_id, storage=storage)

        # 2. Delete Cognito User Pool profile if client is available
        if cognito_client is not None:
            try:
                # Identity accounts might have provider_subject
                identity = await repo.get_identity_account("cognito", str(user_id))
                username = identity.provider_subject if identity else str(user_id)
                cognito_client.admin_delete_user(
                    UserPoolId=getattr(cognito_client, "user_pool_id", "mock-pool"),
                    Username=username,
                )
            except Exception as cog_err:
                logger.warning(f"Cognito user deletion warning: {cog_err}")

        # 3. Finalize job status
        stmt = (
            update(AccountDeletionJob)
            .where(AccountDeletionJob.id == job_id)
            .values(status="COMPLETED", completed_at=datetime.now(UTC))
        )
        await repo._db.execute(stmt)
        await repo._db.commit()

        logger.info(f"Successfully completed account deletion job {job_id} for user {user_id}")
        return {
            "status": "completed",
            "job_id": str(job_id),
            "user_id": str(user_id),
            "erasure": erasure_res,
        }

    except Exception as exc:
        logger.exception(f"Error executing account deletion job {job_id}: {exc}")
        job.attempts += 1
        job.last_error_code = type(exc).__name__
        job.last_error_message = str(exc)
        job.status = "FAILED" if job.attempts >= job.max_attempts else "RETRY"

        # Revert user status to DELETION_PENDING so it can be retried
        if job.status == "RETRY":
            await repo.update_user_status(
                user_id=user_id,
                status=AccountStatus.DELETION_PENDING.value,
            )

        await repo._db.commit()
        raise
