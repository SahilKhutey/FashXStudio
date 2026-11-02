from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import ConsentRequiredError, EntityNotFoundError, ValidationError
from fashx.core.settings import get_settings
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.errors import ApiError
from fashx.tryon.cache_key import compute_tryon_cache_key
from fashx.tryon.ports import TryOnModelAdapterPort
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork


@dataclass(frozen=True)
class CreateTryOnCommand:
    user_id: UUID
    garment_id: UUID
    idempotency_key: str
    photo_id: UUID | None = None
    render_config: dict[str, Any] | None = None


@dataclass(frozen=True)
class CreateTryOnResult:
    job_id: UUID
    status: str
    artifact_key: str
    reused: bool
    is_cached: bool = False
    result_url: str | None = None


class CreateTryOnJobUseCase:
    """Validates inputs, source clearance, and user consent, then persists an asynchronous queued try-on job."""

    def __init__(
        self,
        tryon_uow: TryOnUnitOfWork,
        profile_uow: ProfileUnitOfWork,
        catalog_uow: CatalogUnitOfWork,
        adapter: TryOnModelAdapterPort | None = None,
        *,
        model_version: str | None = None,
        pipeline_version: str | None = None,
    ) -> None:
        self.tryon_uow = tryon_uow
        self.profile_uow = profile_uow
        self.catalog_uow = catalog_uow
        if adapter is not None:
            self.adapter = adapter
            self.model_version = model_version or adapter.model_version
            self.pipeline_version = pipeline_version or adapter.pipeline_version
        else:
            from fashx.core.dependencies import get_tryon_adapter

            self.adapter = get_tryon_adapter()
            self.model_version = model_version or self.adapter.model_version
            self.pipeline_version = pipeline_version or self.adapter.pipeline_version

    async def execute(self, cmd: CreateTryOnCommand) -> CreateTryOnResult:
        settings = get_settings()

        # 1. User & Consent Verification
        async with self.profile_uow:
            user = await self.profile_uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            has_consent = await self.profile_uow.consents.has_consent(cmd.user_id, "body_photo")
            if not has_consent:
                raise ConsentRequiredError("body_photo")

            # 2. Portrait Photo Ownership & Quality Verification
            if cmd.photo_id is not None:
                photo = await self.profile_uow.photos.get_owned(cmd.photo_id, cmd.user_id)
                if photo is None:
                    raise ValidationError("Photo not found or not owned by user", field="photo_id")
            else:
                photo = await self.profile_uow.photos.get_active_photo(
                    cmd.user_id, "tryon_reference"
                )
                if photo is None:
                    raise ValidationError(
                        "User does not have an active portrait photo uploaded.", field="photo"
                    )

            if photo.status != "accepted":
                raise ValidationError(
                    f"User portrait photo status is '{photo.status}'; must be 'accepted' to run try-on.",
                    field="photo_status",
                )

            photo_id = photo.id
            photo_version = getattr(photo, "version", 1)
            photo_hash = getattr(photo, "content_sha256", None) or photo.storage_key

        # 3. Garment Eligibility & Source Rights Verification
        async with self.catalog_uow:
            garment = await self.catalog_uow.canonical_garments.get_by_id(cmd.garment_id)
            if garment is None:
                raise EntityNotFoundError("CanonicalGarment", cmd.garment_id)

            if getattr(garment, "tryon_supported", True) is False:
                raise ApiError(
                    422, "unsupported_garment", "Try-on is not supported for this garment type"
                )

            if (
                settings.tryon_supported_categories
                and garment.category not in settings.tryon_supported_categories
            ):
                raise ApiError(
                    422,
                    "unsupported_garment",
                    f"Try-on is not supported for category '{garment.category}'",
                )

            # Check live source rights
            if hasattr(self.catalog_uow, "merchant_products") and hasattr(
                self.catalog_uow, "sources"
            ):
                products = await self.catalog_uow.merchant_products.get_by_canonical_garment_id(
                    garment.id
                )
                if products:
                    for prod in products:
                        if prod.source_id:
                            src = await self.catalog_uow.sources.get_by_id(prod.source_id)
                            if src and (src.status != "cleared" or not src.rights_tryon):
                                raise ApiError(
                                    422,
                                    "source_rights_revoked",
                                    "Garment catalog source does not permit virtual try-on",
                                )

            garment_id = garment.id
            garment_version = garment.version

        # 4. Compute Deterministic Composite Cache Key
        artifact_key = compute_tryon_cache_key(
            user_photo_hash=photo_hash,
            garment_id=garment_id,
            garment_version=garment_version,
            model_version=self.model_version,
            pipeline_version=self.pipeline_version,
            render_config=cmd.render_config,
        )

        async with self.tryon_uow:
            # 5. Check Idempotency
            existing_job = await self.tryon_uow.jobs.get_by_user_and_idempotency(
                cmd.user_id, cmd.idempotency_key
            )
            if existing_job is not None:
                artifact = await self.tryon_uow.artifacts.get_by_artifact_key(
                    existing_job.artifact_key
                )
                return CreateTryOnResult(
                    job_id=existing_job.id,
                    status=existing_job.status,
                    artifact_key=existing_job.artifact_key,
                    reused=True,
                    is_cached=existing_job.status == "completed",
                    result_url=artifact.result_key if artifact else None,
                )

            # 6. Check Instant Cache Hit
            cached_artifact = await self.tryon_uow.artifacts.get_by_artifact_key(artifact_key)
            if cached_artifact is not None:
                return CreateTryOnResult(
                    job_id=cached_artifact.job_id,
                    status="completed",
                    artifact_key=artifact_key,
                    reused=False,
                    is_cached=True,
                    result_url=cached_artifact.result_key,
                )

            # 7. Check Daily User Cap & Budget (Rule I08)
            from fashx.ml.breaker import check_daily_budget_exceeded, check_user_daily_cap_exceeded

            if hasattr(self.tryon_uow, "session") and self.tryon_uow.session:
                if await check_daily_budget_exceeded(
                    self.tryon_uow.session, settings.tryon_daily_budget_usd
                ):
                    raise ApiError(503, "service_unavailable", "Try-on is at capacity today")
                if await check_user_daily_cap_exceeded(
                    self.tryon_uow.session, cmd.user_id, settings.tryon_user_daily_cap
                ):
                    raise ApiError(429, "rate_limit_exceeded", "Daily try-on cap exceeded")

            # 8. Persist Queued Job with Race Condition Safety
            try:
                job = await self.tryon_uow.jobs.create(
                    user_id=cmd.user_id,
                    garment_id=garment_id,
                    profile_photo_id=photo_id,
                    idempotency_key=cmd.idempotency_key,
                    artifact_key=artifact_key,
                    model_version=self.model_version,
                    pipeline_version=self.pipeline_version,
                    photo_version=photo_version,
                    garment_version=garment_version,
                    provider=getattr(self.adapter, "provider", "mock"),
                )
                await self.tryon_uow.commit()
            except IntegrityError:
                # Concurrent race condition: another request won the unique constraint
                await self.tryon_uow.rollback()
                winning_job = await self.tryon_uow.jobs.get_by_user_and_idempotency(
                    cmd.user_id, cmd.idempotency_key
                )
                if winning_job is not None:
                    artifact = await self.tryon_uow.artifacts.get_by_artifact_key(
                        winning_job.artifact_key
                    )
                    return CreateTryOnResult(
                        job_id=winning_job.id,
                        status=winning_job.status,
                        artifact_key=winning_job.artifact_key,
                        reused=True,
                        is_cached=winning_job.status == "completed",
                        result_url=artifact.result_key if artifact else None,
                    )
                raise

        return CreateTryOnResult(
            job_id=job.id,
            status="queued",
            artifact_key=artifact_key,
            reused=False,
            is_cached=False,
            result_url=None,
        )
