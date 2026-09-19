import pytest
from api.app.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from api.app.profile.application.update_preferences import (
    UpdatePreferencesCommand,
    UpdatePreferencesUseCase,
)
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.mark.asyncio
async def test_update_preferences_lifecycle(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)

    # 1. Create user
    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(CreateProfileCommand())

    # 2. Update preferences
    pref_uc = UpdatePreferencesUseCase(uow)
    cmd = UpdatePreferencesCommand(
        user_id=profile.user_id,
        colors_favored=["navy", "olive", "white"],
        colors_avoided=["yellow", "neon"],
        categories=["tops", "outerwear"],
        budget_min=1000,
        budget_max=15000,
    )
    res = await pref_uc.execute(cmd)

    assert res.user_id == profile.user_id
    assert res.colors_favored == ["navy", "olive", "white"]
    assert res.colors_avoided == ["yellow", "neon"]
    assert res.categories == ["tops", "outerwear"]
    assert res.budget_min == 1000
    assert res.budget_max == 15000

    # 3. Idempotently update again
    cmd_update = UpdatePreferencesCommand(
        user_id=profile.user_id,
        colors_favored=["navy", "black"],
        colors_avoided=["yellow"],
        categories=["tops"],
        budget_min=2000,
        budget_max=20000,
    )
    res2 = await pref_uc.execute(cmd_update)
    assert res2.colors_favored == ["navy", "black"]
    assert res2.budget_max == 20000
