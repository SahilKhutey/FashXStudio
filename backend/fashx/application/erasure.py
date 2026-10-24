from __future__ import annotations

import hashlib
import hmac
import inspect
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import UUID as SqlUUID
from sqlalchemy import bindparam, text

from fashx.core.events import StoragePurgeRequested
from fashx.integration.outbox import OutboxMessage

# Single source of truth for table classification (Rule I16, Gate G4)
BIOMETRIC_TABLES: list[str] = [
    "tryon_jobs",
    "profile_artifacts",
    "profile_photo_jobs",
    "skin_tone_results",
    "media_objects",
    "user_photos",
    "body_profiles",
    "user_measurements",
    "user_style_profiles",
]

ACCOUNT_TABLES: list[str] = [
    "wardrobe_items",
    "buy_clicks",
    "fit_feedback",
    "tryon_feedback",
    "feed_exclusions",
    "feed_impressions",
    "feed_signals",
    "user_preferences",
    "onboarding_profiles",
    "consent_records",
    "style_quiz_picks",
    "idempotency_records",
    "pilot_participants",
    "pilot_survey_responses",
    "pilot_feedback",
    "experiment_exposures",
    "tenant_members",
]

CORE_AUTH: list[str] = [
    "auth_identities",
    "users",
]

ANONYMIZE_TABLES: list[str] = [
    "domain_events",
    "pilot_invites",
]

# Minimal pseudonymous tombstones to prevent resurrection on backup restore (Rule 9.8)
RETAINED_MINIMAL: list[str] = [
    "erasure_tombstones",
]


class ErasureIncomplete(RuntimeError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


async def _exec(
    session: Any,
    sql: str,
    uid: UUID,
    label: str,
    counts: dict[str, int],
) -> None:
    res = session.execute(text(sql).bindparams(bindparam("uid", uid, type_=SqlUUID)))
    if inspect.isawaitable(res):
        res = await res
    rc = getattr(res, "rowcount", None)
    counts[label] = rc if isinstance(rc, int) and rc >= 0 else 0


async def _write_tombstone(session: Any, user_id: UUID) -> None:
    res = session.execute(
        text(
            'INSERT INTO "erasure_tombstones" (user_id, erased_at) '
            "VALUES (:uid, :erased_at) ON CONFLICT (user_id) DO NOTHING"
        ).bindparams(
            bindparam("uid", user_id, type_=SqlUUID),
            bindparam("erased_at", datetime.now(UTC)),
        )
    )
    if inspect.isawaitable(res):
        await res


async def erase_biometrics(
    uow: Any,
    user_id: UUID,
    storage: Any | None = None,
    record_revocation: bool = True,
) -> dict[str, Any]:
    """Rule I16 & Gate G4: Instantly cascades deletion of biometric rows and enqueues object purging."""
    counts: dict[str, int] = {}

    # 1. Revoke consent in consent_records if requested
    if record_revocation and getattr(uow, "consents", None) is not None:
        res = uow.consents.upsert(user_id=user_id, data_type="body_photo", granted=False)
        if inspect.isawaitable(res):
            await res

    # 2. Collect storage keys for user
    keys: list[str] = []
    if getattr(uow, "media", None) is not None:
        records = uow.media.list_for_user(user_id)
        if inspect.isawaitable(records):
            records = await records
        keys.extend([r.object_key for r in records if r.object_key])

    if getattr(uow, "photos", None) is not None:
        photos = uow.photos.list_for_user(user_id)
        if inspect.isawaitable(photos):
            photos = await photos
        keys.extend([p.storage_key for p in photos if p.storage_key])

    # 3. Delete from biometric tables without swallowing errors
    session = getattr(uow, "session", None)
    if session is not None:
        for tbl in BIOMETRIC_TABLES:
            await _exec(
                session,
                f'DELETE FROM "{tbl}" WHERE user_id = :uid',
                user_id,
                tbl,
                counts,
            )
    else:
        # Fallback for in-memory / unit-of-work mocks
        if getattr(uow, "photos", None) is not None:
            photos = uow.photos.list_for_user(user_id)
            if inspect.isawaitable(photos):
                photos = await photos
            for p in photos:
                del_res = uow.photos.delete(p)
                if inspect.isawaitable(del_res):
                    await del_res

        if getattr(uow, "body_profiles", None) is not None:
            bp = uow.body_profiles.get_by_user_id(user_id)
            if inspect.isawaitable(bp):
                bp = await bp
            if bp:
                del_res = uow.body_profiles.delete(bp)
                if inspect.isawaitable(del_res):
                    await del_res

    # 4. Enqueue storage purge via Outbox
    prefix = f"u/{user_id}/"
    if getattr(uow, "outbox", None) is not None:
        msg = OutboxMessage(
            id=uuid4(),
            event=StoragePurgeRequested(
                prefix=prefix,
                user_id=user_id,
                reason="consent_revoked",
            ),
            created_at=datetime.now(UTC),
        )
        add_res = uow.outbox.add(msg)
        if inspect.isawaitable(add_res):
            await add_res

    # If storage passed directly, prune immediately
    if storage is not None:
        if hasattr(storage, "delete_prefix"):
            storage.delete_prefix(prefix)
        for k in keys:
            if hasattr(storage, "delete"):
                storage.delete(k)

    return {
        "user_id": str(user_id),
        "status": "biometrics_erased",
        "keys_queued": len(keys),
        "counts": counts,
    }


async def erase_account(
    uow: Any,
    user_id: UUID,
    storage: Any | None = None,
) -> dict[str, Any]:
    """Right to Erasure (DPDP/GDPR): hard-deletes all user data, anonymizes logs, and purges bucket."""
    session = getattr(uow, "session", None)
    counts: dict[str, int] = {}
    prefix = f"u/{user_id}/"

    if session is not None:
        # Use a SAVEPOINT so that a rollback on failure only undoes the erasure
        # work, not the caller's outer transaction (important for tests and for
        # production callers that hold an open unit-of-work).
        nested = None
        if hasattr(session, "begin_nested"):
            nested = session.begin_nested()
            if inspect.isawaitable(nested):
                nested = await nested
        try:
            # 1. Erase biometrics first (skip revocation logging for whole-account erasure)
            bio_res = await erase_biometrics(uow, user_id, storage=storage, record_revocation=False)
            counts.update(bio_res.get("counts", {}))

            # 2. Anonymize event logs
            for tbl in ANONYMIZE_TABLES:
                await _exec(
                    session,
                    f'UPDATE "{tbl}" SET user_id = NULL WHERE user_id = :uid',
                    user_id,
                    tbl,
                    counts,
                )

            # 3. Hard-delete user account tables
            for tbl in ACCOUNT_TABLES:
                await _exec(
                    session,
                    f'DELETE FROM "{tbl}" WHERE user_id = :uid',
                    user_id,
                    tbl,
                    counts,
                )

            # 4. Delete auth identities & canonical user
            await _exec(
                session,
                'DELETE FROM "auth_identities" WHERE user_id = :uid',
                user_id,
                "auth_identities",
                counts,
            )
            await _exec(
                session,
                'DELETE FROM "users" WHERE id = :uid',
                user_id,
                "users",
                counts,
            )

            # 5. Record minimal pseudonymous tombstone
            await _write_tombstone(session, user_id)

            # 6. Enqueue full storage deletion task in outbox in the same transaction
            if getattr(uow, "outbox", None) is not None:
                msg = OutboxMessage(
                    id=uuid4(),
                    event=StoragePurgeRequested(
                        prefix=prefix,
                        user_id=user_id,
                        reason="account_erased",
                    ),
                    created_at=datetime.now(UTC),
                )
                add_res = uow.outbox.add(msg)
                if inspect.isawaitable(add_res):
                    await add_res

            # 7. Commit the savepoint, then flush to the outer transaction
            if nested is not None and hasattr(nested, "commit"):
                commit_res = nested.commit()
                if inspect.isawaitable(commit_res):
                    await commit_res

            if hasattr(uow, "commit"):
                res = uow.commit()
                if inspect.isawaitable(res):
                    await res
            elif hasattr(session, "commit"):
                res = session.commit()
                if inspect.isawaitable(res):
                    await res
        except Exception as e:
            # Roll back only to the savepoint; the caller's outer transaction
            # is preserved so no half-deleted state leaks into the session.
            if nested is not None and hasattr(nested, "rollback"):
                rb_res = nested.rollback()
                if inspect.isawaitable(rb_res):
                    await rb_res
            elif hasattr(uow, "rollback"):
                rb_res = uow.rollback()
                if inspect.isawaitable(rb_res):
                    await rb_res
            elif hasattr(session, "rollback"):
                rb_res = session.rollback()
                if inspect.isawaitable(rb_res):
                    await rb_res
            raise ErasureIncomplete([f"{type(e).__name__}: {e}"]) from e

        if hasattr(session, "expunge_all"):
            session.expunge_all()
    else:
        # Fallback for mock unit-of-work
        bio_res = await erase_biometrics(uow, user_id, storage=storage, record_revocation=False)
        counts.update(bio_res.get("counts", {}))
        if getattr(uow, "outbox", None) is not None:
            msg = OutboxMessage(
                id=uuid4(),
                event=StoragePurgeRequested(
                    prefix=prefix,
                    user_id=user_id,
                    reason="account_erased",
                ),
                created_at=datetime.now(UTC),
            )
            add_res = uow.outbox.add(msg)
            if inspect.isawaitable(add_res):
                await add_res

    if storage is not None and hasattr(storage, "delete_prefix"):
        storage.delete_prefix(prefix)

    return {
        "user_id": str(user_id),
        "status": "account_erased",
        "counts": counts,
    }


def execute_storage_erasure_task(
    payload: dict[str, Any],
    storage: Any,
    server_secret: bytes = b"fashx-erasure-audit-secret",
) -> str:
    """Worker task execution: purges object store prefix and returns anonymized HMAC audit hash."""
    prefix = payload.get("prefix", "")
    keys = payload.get("keys", [])
    user_id = payload.get("user_id", "")

    if storage:
        if keys:
            for k in keys:
                try:
                    storage.delete(k)
                except Exception:
                    pass
        if prefix:
            try:
                storage.delete_prefix(prefix)
            except Exception:
                pass

    user_hash = hmac.new(server_secret, user_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return user_hash
