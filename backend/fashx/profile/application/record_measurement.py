from dataclasses import dataclass
from uuid import UUID

from database.models.profile import UserMeasurement
from schemas.common.enums import DataType, MeasurementSource

from fashx.core.errors import ConsentRequiredError, EntityNotFoundError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


@dataclass
class RecordMeasurementCommand:
    user_id: UUID
    measurement: str
    value: float
    unit: str
    source: MeasurementSource | str
    confidence: float | None = None


class RecordMeasurementUseCase:
    """Use case to validate consent and record physical biometric measurements."""

    def __init__(self, uow: ProfileUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: RecordMeasurementCommand) -> UserMeasurement:
        async with self.uow:
            user = await self.uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            # Rule I07 / GDPR Consent Check: recording measurements requires consent
            consent = await self.uow.consents.get_by_user_and_type(
                cmd.user_id, DataType.MEASUREMENTS.value
            )
            if consent is None or not consent.granted:
                raise ConsentRequiredError(
                    data_type=DataType.MEASUREMENTS.value,
                    message=f"User {cmd.user_id} has not granted consent for '{DataType.MEASUREMENTS.value}'.",
                )

            source_str = cmd.source.value if hasattr(cmd.source, "value") else str(cmd.source)
            record = UserMeasurement(
                user_id=cmd.user_id,
                measurement=cmd.measurement,
                value=cmd.value,
                unit=cmd.unit,
                source=source_str,
                confidence=cmd.confidence,
            )
            self.uow.measurements.add(record)
            await self.uow.commit()

            return record
