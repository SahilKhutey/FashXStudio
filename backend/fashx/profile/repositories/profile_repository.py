from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.identity import ConsentEvent, ConsentRecord, User, UserPhoto
from database.models.media import MediaObject
from database.models.profile import BodyProfile, OnboardingProfile, UserMeasurement, UserPreference
from fashx.core.repository import BaseRepository
from fashx.core.unit_of_work import SqlAlchemyUnitOfWork


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)


class UserConsentRepository(BaseRepository[ConsentRecord]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ConsentRecord)

    async def get_by_user_and_type(self, user_id: UUID, data_type: str) -> ConsentRecord | None:
        return await self.session.get(ConsentRecord, (user_id, data_type))

    async def list_for_user(self, user_id: UUID) -> Sequence[ConsentRecord]:
        stmt = select(ConsentRecord).where(ConsentRecord.user_id == user_id)
        result = await self.session.scalars(stmt)
        return result.all()

    async def has_consent(self, user_id: UUID, data_type: str) -> bool:
        record = await self.get_by_user_and_type(user_id, data_type)
        return bool(record and record.granted)

    async def record_consent_event(
        self,
        user_id: UUID,
        data_type: str,
        granted: bool,
        consent_version: str = "2026.1",
        policy_url: str | None = None,
        decision_source: str = "api",
    ) -> ConsentEvent:
        event = ConsentEvent(
            user_id=user_id,
            data_type=data_type,
            granted=granted,
            consent_version=consent_version,
            policy_url=policy_url,
            decision_source=decision_source,
        )
        self.session.add(event)
        return event

    async def list_events_for_user(self, user_id: UUID) -> Sequence[ConsentEvent]:
        stmt = (
            select(ConsentEvent)
            .where(ConsentEvent.user_id == user_id)
            .order_by(ConsentEvent.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def upsert(
        self,
        user_id: UUID,
        data_type: str,
        granted: bool,
        is_18_or_older: bool | None = None,
        consent_version: str = "2026.1",
        decision_source: str = "api",
        policy_url: str | None = None,
    ) -> ConsentRecord:
        effective_age = is_18_or_older if is_18_or_older is not None else (True if granted else None)
        record = await self.get_by_user_and_type(user_id, data_type)
        if record is not None:
            record.granted = granted
            record.consent_version = consent_version
            record.updated_at = datetime.now(UTC)
            if effective_age is not None:
                record.is_18_or_older = effective_age
        else:
            record = ConsentRecord(
                user_id=user_id,
                data_type=data_type,
                granted=granted,
                consent_version=consent_version,
                is_18_or_older=effective_age,
            )
            self.add(record)

        await self.record_consent_event(
            user_id=user_id,
            data_type=data_type,
            granted=granted,
            consent_version=consent_version,
            policy_url=policy_url,
            decision_source=decision_source,
        )
        return record

    async def record_mobile_consent(
        self,
        user_id: UUID,
        consent_version: str,
        is_18_or_older: bool = True,
        accepts_terms: bool = True,
        accepts_body_photo: bool = True,
    ) -> tuple[ConsentRecord, ConsentRecord]:
        now_terms = datetime.now(UTC)
        terms_rec = await self.get_by_user_and_type(user_id, "terms_and_privacy")
        if terms_rec is not None:
            terms_rec.granted = accepts_terms
            terms_rec.consent_version = consent_version
            terms_rec.is_18_or_older = is_18_or_older
            terms_rec.consented_at = now_terms
            terms_rec.updated_at = now_terms
        else:
            terms_rec = ConsentRecord(
                user_id=user_id,
                data_type="terms_and_privacy",
                granted=accepts_terms,
                consent_version=consent_version,
                is_18_or_older=is_18_or_older,
                consented_at=now_terms,
                updated_at=now_terms,
            )
            self.add(terms_rec)

        now_photo = datetime.now(UTC)
        body_photo_rec = await self.get_by_user_and_type(user_id, "body_photo")
        if body_photo_rec is not None:
            body_photo_rec.granted = accepts_body_photo
            body_photo_rec.consent_version = consent_version
            body_photo_rec.is_18_or_older = is_18_or_older
            body_photo_rec.consented_at = now_photo
            body_photo_rec.updated_at = now_photo
        else:
            body_photo_rec = ConsentRecord(
                user_id=user_id,
                data_type="body_photo",
                granted=accepts_body_photo,
                consent_version=consent_version,
                is_18_or_older=is_18_or_older,
                consented_at=now_photo,
                updated_at=now_photo,
            )
            self.add(body_photo_rec)

        await self.record_consent_event(
            user_id=user_id,
            data_type="terms_and_privacy",
            granted=accepts_terms,
            consent_version=consent_version,
            decision_source="mobile_onboarding",
        )
        await self.record_consent_event(
            user_id=user_id,
            data_type="body_photo",
            granted=accepts_body_photo,
            consent_version=consent_version,
            decision_source="mobile_onboarding",
        )

        return terms_rec, body_photo_rec



class BodyProfileRepository(BaseRepository[BodyProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BodyProfile)

    async def get_by_user_id(self, user_id: UUID) -> BodyProfile | None:
        return await self.session.get(BodyProfile, user_id)

    async def upsert(
        self,
        user_id: UUID,
        height_cm: int | None = None,
        weight_kg: int | None = None,
        build: str | None = None,
    ) -> BodyProfile:
        profile = await self.get_by_user_id(user_id)
        if profile is not None:
            if height_cm is not None:
                profile.height_cm = height_cm
            if weight_kg is not None:
                profile.weight_kg = weight_kg
            if build is not None:
                profile.build = build
            profile.version += 1
            return profile

        profile = BodyProfile(
            user_id=user_id,
            height_cm=height_cm,
            weight_kg=weight_kg,
            build=build,
            version=1,
        )
        self.add(profile)
        return profile


class UserMeasurementRepository(BaseRepository[UserMeasurement]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserMeasurement)

    async def list_by_user_id(self, user_id: UUID) -> Sequence[UserMeasurement]:
        stmt = select(UserMeasurement).where(UserMeasurement.user_id == user_id)
        result = await self.session.scalars(stmt)
        return result.all()


class UserPhotoRepository(BaseRepository[UserPhoto]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserPhoto)

    async def list_for_user(self, user_id: UUID) -> Sequence[UserPhoto]:
        stmt = (
            select(UserPhoto)
            .where(UserPhoto.user_id == user_id)
            .order_by(UserPhoto.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def get_active_photo(self, user_id: UUID, photo_type: str) -> UserPhoto | None:
        stmt = (
            select(UserPhoto)
            .where(
                UserPhoto.user_id == user_id,
                UserPhoto.photo_type == photo_type,
                UserPhoto.status == "accepted",
            )
            .order_by(UserPhoto.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return result.first()

    async def get_owned(self, photo_id: UUID, user_id: UUID) -> UserPhoto | None:
        stmt = select(UserPhoto).where(
            UserPhoto.id == photo_id,
            UserPhoto.user_id == user_id,
        )
        return (await self.session.scalars(stmt)).first()


class UserPreferenceRepository(BaseRepository[UserPreference]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserPreference)

    async def get_by_user_id(self, user_id: UUID) -> UserPreference | None:
        return await self.session.get(UserPreference, user_id)

    async def upsert_preferences(
        self,
        user_id: UUID,
        colors_favored: list[str],
        colors_avoided: list[str],
        categories: list[str],
        budget_min: int | None = None,
        budget_max: int | None = None,
    ) -> UserPreference:
        pref = await self.get_by_user_id(user_id)
        if pref is not None:
            pref.colors_favored = colors_favored
            pref.colors_avoided = colors_avoided
            pref.categories = categories
            pref.budget_min = budget_min
            pref.budget_max = budget_max
            return pref

        pref = UserPreference(
            user_id=user_id,
            colors_favored=colors_favored,
            colors_avoided=colors_avoided,
            categories=categories,
            budget_min=budget_min,
            budget_max=budget_max,
        )
        self.add(pref)
        return pref

    async def upsert(
        self,
        user_id: UUID,
        colors_favored: list[str] | None = None,
        colors_avoided: list[str] | None = None,
        categories: list[str] | None = None,
        budget_min: int | None = None,
        budget_max: int | None = None,
    ) -> UserPreference:
        return await self.upsert_preferences(
            user_id=user_id,
            colors_favored=colors_favored or [],
            colors_avoided=colors_avoided or [],
            categories=categories or [],
            budget_min=budget_min,
            budget_max=budget_max,
        )


class OnboardingProfileRepository(BaseRepository[OnboardingProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OnboardingProfile)

    async def get_by_user_id(self, user_id: UUID) -> OnboardingProfile | None:
        return await self.session.get(OnboardingProfile, user_id)

    async def create_if_missing(self, user_id: UUID) -> OnboardingProfile:
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            profile = OnboardingProfile(user_id=user_id)
            self.add(profile)
            await self.flush()
        return profile


class MediaRepository(BaseRepository[MediaObject]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MediaObject)

    async def get_by_id_and_user(self, media_id: UUID, user_id: UUID) -> MediaObject | None:
        stmt = select(MediaObject).where(MediaObject.id == media_id, MediaObject.user_id == user_id)
        result = await self.session.scalars(stmt)
        return result.first()

    async def list_for_user(self, user_id: UUID, kind: str | None = None) -> Sequence[MediaObject]:
        stmt = select(MediaObject).where(MediaObject.user_id == user_id)
        if kind:
            stmt = stmt.where(MediaObject.kind == kind)
        result = await self.session.scalars(stmt)
        return result.all()

    async def keys_derived_from_photo(self, photo_id: UUID) -> list[str]:
        from database.models.identity import UserPhoto
        from database.models.tryon import TryOnArtifact, TryOnJob

        keys: set[str] = set()

        photo = await self.session.get(UserPhoto, photo_id)
        if photo and photo.storage_key:
            keys.add(photo.storage_key)

        # Media objects directly matching photo_id or containing photo_id in key (thumbnails, sanitized copies)
        media_stmt = select(MediaObject).where(
            (MediaObject.id == photo_id) | (MediaObject.object_key.like(f"%{photo_id}%"))
        )
        media_objs = (await self.session.scalars(media_stmt)).all()
        for m in media_objs:
            keys.add(m.object_key)

        # Derived try-on jobs
        jobs_stmt = select(TryOnJob).where(TryOnJob.profile_photo_id == photo_id)
        jobs = (await self.session.scalars(jobs_stmt)).all()
        for j in jobs:
            if j.artifact_key:
                keys.add(j.artifact_key)

        job_ids = [j.id for j in jobs]
        if job_ids:
            art_stmt = select(TryOnArtifact).where(TryOnArtifact.job_id.in_(job_ids))
            artifacts = (await self.session.scalars(art_stmt)).all()
            for art in artifacts:
                if art.artifact_key:
                    keys.add(art.artifact_key)
                if art.result_key:
                    keys.add(art.result_key)

        # Also find any media objects matching these artifact/result keys
        if keys:
            job_media_stmt = select(MediaObject).where(
                MediaObject.object_key.in_(list(keys))
            )
            job_media = (await self.session.scalars(job_media_stmt)).all()
            for m in job_media:
                keys.add(m.object_key)

        return sorted(keys)

    async def delete_for_photo(self, photo_id: UUID) -> None:
        from sqlalchemy import delete
        keys = await self.keys_derived_from_photo(photo_id)
        if keys:
            stmt = delete(MediaObject).where(MediaObject.object_key.in_(keys))
            await self.session.execute(stmt)


class ProfileUnitOfWork(SqlAlchemyUnitOfWork):
    """Unit of Work bundling Profile aggregate repositories."""

    def __init__(
        self,
        session_factory: (
            Callable[[], AsyncSession] | async_sessionmaker[AsyncSession] | None
        ) = None,
    ) -> None:
        super().__init__(session_factory)
        self._users: UserRepository | None = None
        self._consents: UserConsentRepository | None = None
        self._measurements: UserMeasurementRepository | None = None
        self._photos: UserPhotoRepository | None = None
        self._preferences: UserPreferenceRepository | None = None
        self._onboarding_profiles: OnboardingProfileRepository | None = None
        self._media: MediaRepository | None = None
        self._outbox: Any | None = None

    async def __aenter__(self) -> ProfileUnitOfWork:
        await super().__aenter__()
        self._users = None
        self._consents = None
        self._body_profiles = None
        self._measurements = None
        self._photos = None
        self._preferences = None
        self._onboarding_profiles = None
        self._media = None
        self._outbox = None
        return self

    @property
    def users(self) -> UserRepository:
        if self._users is None:
            self._users = UserRepository(self.session)
        return self._users

    @property
    def consents(self) -> UserConsentRepository:
        if self._consents is None:
            self._consents = UserConsentRepository(self.session)
        return self._consents

    @property
    def body_profiles(self) -> BodyProfileRepository:
        if self._body_profiles is None:
            self._body_profiles = BodyProfileRepository(self.session)
        return self._body_profiles

    @property
    def measurements(self) -> UserMeasurementRepository:
        if self._measurements is None:
            self._measurements = UserMeasurementRepository(self.session)
        return self._measurements

    @property
    def photos(self) -> UserPhotoRepository:
        if self._photos is None:
            self._photos = UserPhotoRepository(self.session)
        return self._photos

    @property
    def preferences(self) -> UserPreferenceRepository:
        if self._preferences is None:
            self._preferences = UserPreferenceRepository(self.session)
        return self._preferences

    @property
    def onboarding_profiles(self) -> OnboardingProfileRepository:
        if self._onboarding_profiles is None:
            self._onboarding_profiles = OnboardingProfileRepository(self.session)
        return self._onboarding_profiles

    @property
    def media(self) -> MediaRepository:
        if self._media is None:
            self._media = MediaRepository(self.session)
        return self._media

    @property
    def outbox(self) -> Any:
        if self._outbox is None:
            from fashx.integration.outbox import SqlOutboxRepository
            self._outbox = SqlOutboxRepository(self.session)
        return self._outbox
