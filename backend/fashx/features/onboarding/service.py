"""F02 application service; persistence is delegated to Core Profile UoW."""

from uuid import UUID

from api.app.core.errors import EntityNotFoundError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork

from .contracts import BasicProfileInput, ContextInput, PreferenceInput, UserContext
from .errors import OnboardingStepError
from .validators import validate_basic_profile, validate_context


class OnboardingService:
    def __init__(self, uow: ProfileUnitOfWork) -> None:
        self.uow = uow

    async def create_or_resume(self, user_id: UUID) -> None:
        async with self.uow:
            if await self.uow.users.get_by_id(user_id) is None:
                raise EntityNotFoundError("User", user_id)
            await self.uow.onboarding_profiles.create_if_missing(user_id)
            await self.uow.commit()

    async def set_basic_profile(self, user_id: UUID, data: BasicProfileInput) -> None:
        validate_basic_profile(data)
        async with self.uow:
            profile = await self.uow.onboarding_profiles.create_if_missing(user_id)
            profile.display_name = data.display_name.strip()
            profile.status = "in_progress"
            profile.step = "style"
            await self.uow.commit()

    async def set_preferences(self, user_id: UUID, data: PreferenceInput) -> None:
        async with self.uow:
            profile = await self.uow.onboarding_profiles.create_if_missing(user_id)
            profile.styles = list(data.styles)
            profile.occasions = list(data.occasions)
            profile.fit_preferences = list(data.fit_preferences)
            profile.shopping_preferences = list(data.shopping_preferences)
            profile.discovery_preferences = list(data.discovery_preferences)
            profile.status, profile.step = "in_progress", "context"
            await self.uow.preferences.upsert_preferences(
                user_id, list(data.colors), [], list(data.categories)
            )
            await self.uow.commit()

    async def set_context(self, user_id: UUID, data: ContextInput) -> None:
        validate_context(data)
        async with self.uow:
            profile = await self.uow.onboarding_profiles.create_if_missing(user_id)
            profile.region = data.region.strip() if data.region else None
            profile.status, profile.step = "in_progress", "review"
            await self.uow.commit()

    async def complete(self, user_id: UUID) -> UserContext:
        async with self.uow:
            profile = await self.uow.onboarding_profiles.create_if_missing(user_id)
            if profile.step != "review":
                raise OnboardingStepError("Cannot complete onboarding before review.")
            profile.status, profile.step = "completed", "review"
            await self.uow.commit()
        return await self.user_context(user_id)

    async def user_context(self, user_id: UUID) -> UserContext:
        async with self.uow:
            profile = await self.uow.onboarding_profiles.get_by_user_id(user_id)
            preferences = await self.uow.preferences.get_by_user_id(user_id)
            if profile is None:
                raise EntityNotFoundError("OnboardingProfile", user_id)
            return UserContext(
                user_id=str(user_id),
                region=profile.region,
                styles=tuple(profile.styles),
                categories=tuple(preferences.categories) if preferences else (),
                colors=tuple(preferences.colors_favored) if preferences else (),
            )
