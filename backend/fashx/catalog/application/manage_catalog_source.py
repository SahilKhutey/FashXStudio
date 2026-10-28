from dataclasses import dataclass
from datetime import date
from uuid import UUID

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError, ValidationError


@dataclass(frozen=True)
class ApproveCatalogSourceCommand:
    source_id: UUID
    rights_display: bool
    rights_tryon: bool
    image_policy: str
    terms_url: str
    terms_checked_on: date


@dataclass(frozen=True)
class CatalogSourceDecision:
    source_id: UUID
    status: str
    rights_display: bool
    rights_tryon: bool
    image_policy: str


class ManageCatalogSourceUseCase:
    """Explicit approval and suspension of a catalog source.

    Call only from a handler that has verified administrator authorization.
    """

    ALLOWED_IMAGE_POLICIES: set[str] = {"hotlink", "mirror"}

    def __init__(self, uow: CatalogUnitOfWork) -> None:
        self.uow = uow

    async def approve_source(self, cmd: ApproveCatalogSourceCommand) -> CatalogSourceDecision:
        """Approve an existing catalog source with explicit display and try-on permissions."""
        if cmd.image_policy not in self.ALLOWED_IMAGE_POLICIES:
            raise ValidationError(
                f"Unsupported image policy '{cmd.image_policy}'; allowed: {sorted(self.ALLOWED_IMAGE_POLICIES)}",
                field="image_policy",
            )

        if cmd.terms_checked_on > date.today():
            raise ValidationError(
                "Terms checked date cannot be in the future",
                field="terms_checked_on",
            )

        if cmd.rights_tryon and not cmd.rights_display:
            raise ValidationError(
                "Cannot grant try-on rights without display rights",
                field="rights_tryon",
            )

        if not cmd.terms_url or not (
            cmd.terms_url.startswith("http://") or cmd.terms_url.startswith("https://")
        ):
            raise ValidationError(
                "Terms URL must be a valid HTTP or HTTPS URL",
                field="terms_url",
            )

        async with self.uow:
            source = await self.uow.sources.get_by_id(cmd.source_id)
            if source is None:
                raise EntityNotFoundError("CatalogSource", cmd.source_id)

            source.status = "cleared"
            source.rights_display = cmd.rights_display
            source.rights_tryon = cmd.rights_tryon
            source.image_policy = cmd.image_policy
            source.terms_url = cmd.terms_url
            source.terms_checked_on = cmd.terms_checked_on

            await self.uow.commit()

            return CatalogSourceDecision(
                source_id=source.id,
                status=source.status,
                rights_display=source.rights_display,
                rights_tryon=source.rights_tryon,
                image_policy=source.image_policy,
            )

    async def suspend_source(
        self, source_id: UUID, reason: str | None = None
    ) -> CatalogSourceDecision:
        """Suspend an approved catalog source and immediately revoke display and try-on rights."""
        async with self.uow:
            source = await self.uow.sources.get_by_id(source_id)
            if source is None:
                raise EntityNotFoundError("CatalogSource", source_id)

            source.status = "suspended"
            source.rights_display = False
            source.rights_tryon = False
            if reason:
                existing_notes = source.notes or ""
                source.notes = f"{existing_notes} | Suspended: {reason}".strip(" |")

            await self.uow.commit()

            return CatalogSourceDecision(
                source_id=source.id,
                status=source.status,
                rights_display=source.rights_display,
                rights_tryon=source.rights_tryon,
                image_policy=source.image_policy,
            )

    async def revoke_tryon_rights(self, source_id: UUID) -> CatalogSourceDecision:
        """Revoke virtual try-on rights while maintaining product display rights."""
        async with self.uow:
            source = await self.uow.sources.get_by_id(source_id)
            if source is None:
                raise EntityNotFoundError("CatalogSource", source_id)

            source.rights_tryon = False
            await self.uow.commit()

            return CatalogSourceDecision(
                source_id=source.id,
                status=source.status,
                rights_display=source.rights_display,
                rights_tryon=source.rights_tryon,
                image_policy=source.image_policy,
            )
