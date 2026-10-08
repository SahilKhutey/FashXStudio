from dataclasses import dataclass, field
from uuid import UUID

from database.models.identity import User
from schemas.identity.consent import ConsentUpdate

from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


@dataclass
class CreateProfileCommand:
    height_cm: int | None = None
    weight_kg: int | None = None
    build: str | None = None
    consents: list[ConsentUpdate] = field(default_factory=list)


@dataclass
class CreateProfileResult:
    user_id: UUID
    height_cm: int | None
    weight_kg: int | None
    build: str | None
    consents: dict[str, bool]


class CreateProfileUseCase:
    """Use case to atomically provision a user account, initial body metrics, and consent scopes."""

    def __init__(self, uow: ProfileUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, cmd: CreateProfileCommand) -> CreateProfileResult:
        async with self.uow:
            user = User()
            self.uow.users.add(user)
            await self.uow.users.flush()

            body_profile = None
            if cmd.height_cm is not None or cmd.weight_kg is not None or cmd.build is not None:
                body_profile = await self.uow.body_profiles.upsert(
                    user_id=user.id,
                    height_cm=cmd.height_cm,
                    weight_kg=cmd.weight_kg,
                    build=cmd.build,
                )

            recorded_consents: dict[str, bool] = {}
            consent_items = (
                [ConsentUpdate(data_type=k, granted=v) for k, v in cmd.consents.items()]
                if isinstance(cmd.consents, dict)
                else cmd.consents
            )
            for item in consent_items:
                dt_str = (
                    item.data_type.value
                    if hasattr(item.data_type, "value")
                    else str(item.data_type)
                )
                rec = await self.uow.consents.upsert(
                    user_id=user.id,
                    data_type=dt_str,
                    granted=item.granted,
                )
                recorded_consents[rec.data_type] = rec.granted

            await self.uow.commit()

            return CreateProfileResult(
                user_id=user.id,
                height_cm=body_profile.height_cm if body_profile else None,
                weight_kg=body_profile.weight_kg if body_profile else None,
                build=body_profile.build if body_profile else None,
                consents=recorded_consents,
            )
