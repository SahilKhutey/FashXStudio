from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.app.core.errors import ConsentRequiredError, EntityNotFoundError
from fashx.profile.application.create_profile import (
    CreateProfileCommand,
    CreateProfileUseCase,
)
from fashx.profile.application.record_measurement import (
    RecordMeasurementCommand,
    RecordMeasurementUseCase,
)
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from schemas.common.enums import BuildType, DataType, MeasurementSource
from schemas.identity.consent import ConsentUpdate


@pytest.mark.asyncio
async def test_create_profile_use_case(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    use_case = CreateProfileUseCase(uow)

    cmd = CreateProfileCommand(
        height_cm=180,
        weight_kg=75,
        build=BuildType.ATHLETIC.value,
        consents=[
            ConsentUpdate(data_type=DataType.MEASUREMENTS, granted=True),
            ConsentUpdate(data_type=DataType.BODY_PHOTO, granted=False),
        ],
    )

    result = await use_case.execute(cmd)
    assert result.user_id is not None
    assert result.height_cm == 180
    assert result.weight_kg == 75
    assert result.build == "athletic"
    assert result.consents.get("measurements") is True
    assert result.consents.get("body_photo") is False

    # Verify directly via repository in a new UoW
    verify_uow = ProfileUnitOfWork(session_factory)
    async with verify_uow:
        body = await verify_uow.body_profiles.get_by_user_id(result.user_id)
        assert body is not None
        assert body.height_cm == 180
        assert body.version == 1

        consent = await verify_uow.consents.get_by_user_and_type(
            result.user_id, DataType.MEASUREMENTS.value
        )
        assert consent is not None
        assert consent.granted is True


@pytest.mark.asyncio
async def test_record_measurement_without_user_raises_not_found(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    use_case = RecordMeasurementUseCase(uow)

    cmd = RecordMeasurementCommand(
        user_id=uuid4(),
        measurement="chest",
        value=102.5,
        unit="cm",
        source=MeasurementSource.USER_ENTERED,
    )

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(cmd)


@pytest.mark.asyncio
async def test_record_measurement_without_consent_raises_consent_required(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    # 1. Create user without measurements consent
    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(CreateProfileCommand())

    # 2. Attempt to record measurement
    record_uc = RecordMeasurementUseCase(uow)
    cmd = RecordMeasurementCommand(
        user_id=profile.user_id,
        measurement="chest",
        value=102.5,
        unit="cm",
        source=MeasurementSource.USER_ENTERED,
    )

    with pytest.raises(ConsentRequiredError) as exc_info:
        await record_uc.execute(cmd)
    assert exc_info.value.data_type == "measurements"


@pytest.mark.asyncio
async def test_record_measurement_with_consent_succeeds(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = ProfileUnitOfWork(session_factory)
    # 1. Create user with measurements consent
    create_uc = CreateProfileUseCase(uow)
    profile = await create_uc.execute(
        CreateProfileCommand(
            consents=[ConsentUpdate(data_type=DataType.MEASUREMENTS, granted=True)]
        )
    )

    # 2. Record measurement
    record_uc = RecordMeasurementUseCase(uow)
    cmd = RecordMeasurementCommand(
        user_id=profile.user_id,
        measurement="waist",
        value=82.0,
        unit="cm",
        source=MeasurementSource.USER_ENTERED,
        confidence=0.95,
    )

    measurement = await record_uc.execute(cmd)
    assert measurement.id is not None
    assert measurement.measurement == "waist"
    assert measurement.value == 82.0
    assert measurement.unit == "cm"
    assert measurement.confidence == 0.95
