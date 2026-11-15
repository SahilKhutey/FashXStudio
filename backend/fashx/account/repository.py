from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.account import AccountDeletionJob, AuthSession, IdentityAccount
from database.models.auth import AuthIdentity, RevokedAuthSession
from database.models.identity import User


class AccountRepository:
    """Persistence repository for User account lifecycle, identity mappings, and sessions."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email_normalized: str) -> User | None:
        stmt = select(User).where(User.email_normalized == email_normalized)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_identity_account(
        self, provider: str, provider_subject: str
    ) -> IdentityAccount | None:
        stmt = select(IdentityAccount).where(
            IdentityAccount.provider == provider,
            IdentityAccount.provider_subject == provider_subject,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def resolve_user(
        self,
        user_id: UUID | None = None,
        provider: str | None = None,
        provider_subject: str | None = None,
    ) -> User | None:
        if user_id:
            user = await self.get_user_by_id(user_id)
            if user is not None:
                return user
        if provider and provider_subject:
            id_acc = await self.get_identity_account(provider, provider_subject)
            if id_acc:
                return await self.get_user_by_id(id_acc.user_id)
        return None

    async def create_or_get_user_for_identity(
        self,
        provider: str,
        provider_subject: str,
        email: str | None = None,
        email_verified: bool = False,
        preferred_user_id: UUID | None = None,
    ) -> tuple[User, IdentityAccount, bool]:
        """Idempotently resolves or provisions a User and linked IdentityAccount."""
        email_norm = email.strip().lower() if email else None

        existing_id = await self.get_identity_account(provider, provider_subject)
        if existing_id is not None:
            user = await self.get_user_by_id(existing_id.user_id)
            if user is None:
                raise RuntimeError(f"Orphaned identity account {existing_id.id} for user {existing_id.user_id}")

            # Reconcile email / verification if newly confirmed
            changed = False
            if email_norm and user.email_normalized != email_norm:
                user.email_normalized = email_norm
                changed = True
            if email_verified and not user.email_verified:
                user.email_verified = True
                if user.status == "PENDING_VERIFICATION":
                    user.status = "ACTIVE"
                    user.activated_at = datetime.now(UTC)
                changed = True

            if changed:
                await self._db.commit()

            return user, existing_id, False

        # Attempt to link by existing email if user already exists
        user: User | None = None
        if email_norm:
            user = await self.get_user_by_email(email_norm)

        is_new = False
        if user is None:
            is_new = True
            user_id = preferred_user_id or uuid4()
            init_status = "ACTIVE" if email_verified else "PENDING_VERIFICATION"
            now = datetime.now(UTC)
            user = User(
                id=user_id,
                status=init_status,
                email_normalized=email_norm,
                email_verified=email_verified,
                activated_at=now if email_verified else None,
            )
            self._db.add(user)

        identity_account = IdentityAccount(
            id=uuid4(),
            user_id=user.id,
            provider=provider,
            provider_subject=provider_subject,
            identity_status="ACTIVE",
            last_authenticated_at=datetime.now(UTC),
        )
        self._db.add(identity_account)

        # Also maintain compatibility with AuthIdentity
        auth_identity = AuthIdentity(
            id=uuid4(),
            issuer=provider,
            subject=provider_subject,
            user_id=user.id,
            role="user",
        )
        self._db.add(auth_identity)

        try:
            await self._db.commit()
            return user, identity_account, is_new
        except IntegrityError:
            # Handle race condition from concurrent login/provision
            await self._db.rollback()
            existing_id = await self.get_identity_account(provider, provider_subject)
            if existing_id is not None:
                user = await self.get_user_by_id(existing_id.user_id)
                if user is not None:
                    return user, existing_id, False
            # If email constraint caused conflict, reload user
            if email_norm:
                user = await self.get_user_by_email(email_norm)
                if user is not None:
                    identity_account = IdentityAccount(
                        id=uuid4(),
                        user_id=user.id,
                        provider=provider,
                        provider_subject=provider_subject,
                        identity_status="ACTIVE",
                    )
                    self._db.add(identity_account)
                    try:
                        await self._db.commit()
                        return user, identity_account, False
                    except IntegrityError:
                        await self._db.rollback()
                        existing_id = await self.get_identity_account(provider, provider_subject)
                        if existing_id is not None:
                            user = await self.get_user_by_id(existing_id.user_id)
                            if user is not None:
                                return user, existing_id, False

            raise

    async def update_user_status(
        self,
        user_id: UUID,
        status: str,
        disabled_at: datetime | None = None,
        deletion_requested_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> User | None:
        user = await self.get_user_by_id(user_id)
        if user is None:
            return None

        user.status = status
        if disabled_at is not None:
            user.disabled_at = disabled_at
        if deletion_requested_at is not None:
            user.deletion_requested_at = deletion_requested_at
        if deleted_at is not None:
            user.deleted_at = deleted_at

        await self._db.commit()
        return user

    async def record_session(
        self,
        user_id: UUID,
        provider: str,
        provider_jti: str,
        expires_at: datetime,
        device_label: str | None = None,
        ip_address: str | None = None,
        provider_origin_jti: str | None = None,
    ) -> AuthSession:
        stmt = select(AuthSession).where(
            AuthSession.provider == provider,
            AuthSession.provider_jti == provider_jti,
        )
        result = await self._db.execute(stmt)
        session = result.scalar_one_or_none()

        now = datetime.now(UTC)
        if session is not None:
            session.last_seen_at = now
            session.device_label = device_label or session.device_label
            session.ip_address = ip_address or session.ip_address
        else:
            session = AuthSession(
                id=uuid4(),
                user_id=user_id,
                provider=provider,
                provider_origin_jti=provider_origin_jti,
                provider_jti=provider_jti,
                device_label=device_label,
                ip_address=ip_address,
                session_status="ACTIVE",
                expires_at=expires_at,
                created_at=now,
                last_seen_at=now,
            )
            self._db.add(session)

        try:
            await self._db.commit()
        except IntegrityError:
            await self._db.rollback()

        return session

    async def revoke_all_sessions(
        self,
        user_id: UUID,
        subject: str,
        provider: str = "cognito",
    ) -> int:
        """Revokes all active sessions for a user in auth_sessions and revoked_auth_sessions."""
        now = datetime.now(UTC)

        # 1. Fetch active sessions to insert into revoked_auth_sessions
        stmt = select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.session_status == "ACTIVE",
        )
        result = await self._db.execute(stmt)
        active_sessions = list(result.scalars().all())

        count = len(active_sessions)
        for s in active_sessions:
            s.session_status = "REVOKED"
            s.revoked_at = now
            # Write to revoked_auth_sessions for fast verifier lookup
            revoked_record = RevokedAuthSession(
                id=uuid4(),
                identity_provider=s.provider,
                subject=subject,
                session_id=s.provider_jti,
                expires_at=s.expires_at,
            )
            self._db.add(revoked_record)

        # Also add a catch-all subject revocation record with a synthetic session ID
        # or mark all auth_identities as disabled
        await self._db.commit()
        return count

    async def create_deletion_job(self, user_id: UUID) -> AccountDeletionJob:
        now = datetime.now(UTC)
        job = AccountDeletionJob(
            id=uuid4(),
            user_id=user_id,
            status="PENDING",
            requested_at=now,
            attempts=0,
        )
        self._db.add(job)

        # Set user state to DELETION_PENDING
        await self.update_user_status(
            user_id=user_id,
            status="DELETION_PENDING",
            deletion_requested_at=now,
        )
        await self._db.commit()
        return job

    async def get_deletion_job(self, job_id: UUID) -> AccountDeletionJob | None:
        stmt = select(AccountDeletionJob).where(AccountDeletionJob.id == job_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_deletion_job_for_user(
        self, user_id: UUID
    ) -> AccountDeletionJob | None:
        stmt = (
            select(AccountDeletionJob)
            .where(AccountDeletionJob.user_id == user_id)
            .order_by(AccountDeletionJob.requested_at.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
