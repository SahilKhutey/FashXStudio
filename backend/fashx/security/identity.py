from dataclasses import dataclass
from typing import Protocol
from uuid import NAMESPACE_DNS, uuid4, uuid5

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class Identity:
    user_id: str
    role: str = "user"
    disabled: bool = False


class IdentityRepo(Protocol):
    async def resolve(self, issuer: str, subject: str) -> Identity: ...
    async def set_role(self, issuer: str, subject: str, role: str) -> None: ...
    async def disable(self, issuer: str, subject: str) -> None: ...


class InMemoryIdentityRepo:
    """In-memory identity repository for unit and hermetic testing."""

    def __init__(self) -> None:
        self._identities: dict[tuple[str, str], Identity] = {}
        self._roles: dict[tuple[str, str], str] = {}
        self._disabled: set[tuple[str, str]] = set()

    async def resolve(self, issuer: str, subject: str) -> Identity:
        key = (issuer, subject)
        if key not in self._identities:
            user_id = str(uuid5(NAMESPACE_DNS, f"{issuer}:{subject}"))
            role = self._roles.get(key, "user")
            is_disabled = key in self._disabled
            self._identities[key] = Identity(
                user_id=user_id,
                role=role,
                disabled=is_disabled,
            )
        return self._identities[key]

    async def set_role(self, issuer: str, subject: str, role: str) -> None:
        key = (issuer, subject)
        self._roles[key] = role
        if key in self._identities:
            curr = self._identities[key]
            self._identities[key] = Identity(
                user_id=curr.user_id,
                role=role,
                disabled=curr.disabled,
            )

    async def disable(self, issuer: str, subject: str) -> None:
        key = (issuer, subject)
        self._disabled.add(key)
        if key in self._identities:
            curr = self._identities[key]
            self._identities[key] = Identity(
                user_id=curr.user_id,
                role=curr.role,
                disabled=True,
            )


class SqlIdentityRepo:
    """SQL-backed identity repository using AsyncSession and AuthIdentity/User models."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def resolve(self, issuer: str, subject: str) -> Identity:
        from database.models.auth import AuthIdentity
        from database.models.identity import User

        stmt = select(AuthIdentity).where(
            AuthIdentity.issuer == issuer,
            AuthIdentity.subject == subject,
        )
        result = await self._db.execute(stmt)
        record = result.scalar_one_or_none()

        if record is not None:
            return Identity(
                user_id=str(record.user_id),
                role=record.role,
                disabled=record.disabled_at is not None,
            )

        # Create new user and linked auth identity
        new_user_id = uuid4()
        user = User(id=new_user_id)
        auth_record = AuthIdentity(
            id=uuid4(),
            issuer=issuer,
            subject=subject,
            user_id=new_user_id,
            role="user",
        )

        try:
            self._db.add(user)
            self._db.add(auth_record)
            await self._db.commit()
            return Identity(
                user_id=str(new_user_id),
                role="user",
                disabled=False,
            )
        except IntegrityError:
            # Race condition handling: identity was inserted concurrently
            await self._db.rollback()
            result = await self._db.execute(stmt)
            record = result.scalar_one()
            return Identity(
                user_id=str(record.user_id),
                role=record.role,
                disabled=record.disabled_at is not None,
            )

    async def set_role(self, issuer: str, subject: str, role: str) -> None:
        from database.models.auth import AuthIdentity

        stmt = (
            update(AuthIdentity)
            .where(
                AuthIdentity.issuer == issuer,
                AuthIdentity.subject == subject,
            )
            .values(role=role)
        )
        await self._db.execute(stmt)
        await self._db.commit()

    async def disable(self, issuer: str, subject: str) -> None:
        from database.models.auth import AuthIdentity

        stmt = (
            update(AuthIdentity)
            .where(
                AuthIdentity.issuer == issuer,
                AuthIdentity.subject == subject,
            )
            .values(disabled_at=func.now())
        )
        await self._db.execute(stmt)
        await self._db.commit()
