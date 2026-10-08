from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.core.repository import BaseRepository
from fashx.core.unit_of_work import SqlAlchemyUnitOfWork
from database.models.identity import ConsentRecord, User, UserPhoto
from database.models.profile import BodyProfile, OnboardingProfile, UserMeasurement, UserPreference


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

    async def upsert(self, user_id: UUID, data_type: str, granted: bool) -> ConsentRecord:
        record = await self.get_by_user_and_type(user_id, data_type)
        if record is not None:
            record.granted = granted
            record.updated_at = datetime.now(UTC)
            return record

        record = ConsentRecord(user_id=user_id, data_type=data_type, granted=granted)
        self.add(record)
        return record


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

    async def __aenter__(self) -> "ProfileUnitOfWork":
        await super().__aenter__()
        self._users = None
        self._consents = None
        self._body_profiles = None
        self._measurements = None
        self._photos = None
        self._preferences = None
        self._onboarding_profiles = None
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
