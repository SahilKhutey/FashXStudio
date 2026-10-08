from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.identity import UserPhoto
from database.models.profile import BodyProfile, ProfileArtifact, SkinToneResult, UserPreference


class ProfileIntelligenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def latest_skin_tone(self, user_id: UUID) -> SkinToneResult | None:
        stmt = select(SkinToneResult).where(SkinToneResult.user_id == user_id).order_by(desc(SkinToneResult.created_at))
        return (await self.session.execute(stmt)).scalars().first()

    async def latest_tryon_photo(self, user_id: UUID) -> UserPhoto | None:
        stmt = (select(UserPhoto).where(UserPhoto.user_id == user_id, UserPhoto.photo_type == "tryon_reference")
                .order_by(desc(UserPhoto.created_at)))
        return (await self.session.execute(stmt)).scalars().first()

    async def current_profile_rows(self, user_id: UUID) -> tuple[BodyProfile | None, UserPreference | None]:
        return await self.session.get(BodyProfile, user_id), await self.session.get(UserPreference, user_id)

    async def next_artifact_version(self, user_id: UUID) -> int:
        stmt = select(ProfileArtifact.version).where(ProfileArtifact.user_id == user_id).order_by(desc(ProfileArtifact.version)).limit(1)
        current = (await self.session.execute(stmt)).scalar_one_or_none()
        return (current or 0) + 1

    async def create_artifact(self, **kwargs) -> ProfileArtifact:
        artifact = ProfileArtifact(**kwargs)
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def latest_artifact(self, user_id: UUID) -> ProfileArtifact | None:
        stmt = select(ProfileArtifact).where(ProfileArtifact.user_id == user_id).order_by(desc(ProfileArtifact.version)).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def upsert_skin_tone(self, **kwargs) -> SkinToneResult:
        existing = await self.session.get(SkinToneResult, kwargs["id"]) if kwargs.get("id") else None
        if existing is None:
            stmt = select(SkinToneResult).where(SkinToneResult.photo_id == kwargs["photo_id"])
            existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing is None:
            existing = SkinToneResult(**kwargs)
            self.session.add(existing)
        else:
            for key, value in kwargs.items():
                if key != "id":
                    setattr(existing, key, value)
        await self.session.flush()
        return existing
