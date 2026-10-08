import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.features.onboarding.contracts import BasicProfileInput, ContextInput, PreferenceInput
from fashx.features.onboarding.errors import OnboardingStepError, ProfileValidationError
from fashx.features.onboarding.service import OnboardingService
from fashx.profile.application.create_profile import CreateProfileCommand, CreateProfileUseCase
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


async def create_user(session_factory: async_sessionmaker[AsyncSession]):
    return await CreateProfileUseCase(ProfileUnitOfWork(session_factory)).execute(CreateProfileCommand())


@pytest.mark.asyncio
async def test_onboarding_persists_mutable_context_through_core_profile_uow(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user(session_factory)
    service = OnboardingService(ProfileUnitOfWork(session_factory))

    await service.create_or_resume(user.user_id)
    await service.set_basic_profile(user.user_id, BasicProfileInput("Asha"))
    await service.set_preferences(
        user.user_id,
        PreferenceInput(styles=("minimal",), categories=("tops",), colors=("navy",)),
    )
    await service.set_context(user.user_id, ContextInput("Bengaluru, IN"))
    context = await service.complete(user.user_id)

    assert context.region == "Bengaluru, IN"
    assert context.styles == ("minimal",)
    assert context.categories == ("tops",)
    assert context.colors == ("navy",)


@pytest.mark.asyncio
async def test_onboarding_validates_name_and_review_gate(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user(session_factory)
    service = OnboardingService(ProfileUnitOfWork(session_factory))
    await service.create_or_resume(user.user_id)

    with pytest.raises(ProfileValidationError):
        await service.set_basic_profile(user.user_id, BasicProfileInput(" "))
    with pytest.raises(OnboardingStepError):
        await service.complete(user.user_id)
