from dataclasses import dataclass, field
from uuid import UUID

from database.models.profile import UserPreference

from api.app.core.errors import EntityNotFoundError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


@dataclass
class UpdatePreferencesCommand:
    user_id: UUID
    colors_favored: list[str] = field(default_factory=list)
    colors_avoided: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    budget_min: int | None = None
    budget_max: int | None = None


class UpdatePreferencesUseCase:
    """Use case to persist and update user styling preferences and shopping constraints."""

    def __init__(self, uow: ProfileUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: UpdatePreferencesCommand) -> UserPreference:
        async with self.uow:
            user = await self.uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            pref = await self.uow.preferences.upsert_preferences(
                user_id=cmd.user_id,
                colors_favored=cmd.colors_favored,
                colors_avoided=cmd.colors_avoided,
                categories=cmd.categories,
                budget_min=cmd.budget_min,
                budget_max=cmd.budget_max,
            )
            await self.uow.flush()
            await self.uow.commit()

            return pref
