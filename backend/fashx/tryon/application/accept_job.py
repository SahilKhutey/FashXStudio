"""AcceptTryOnJobUseCase: Request acceptance, security checks, idempotency, and transactional outbox persistence (Phase 07.4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.errors import EntityNotFoundError, ValidationError
from fashx.core.settings import get_settings
from fashx.integration.outbox import SqlOutboxRepository
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.errors import ApiError
from fashx.tryon.cache_key import compute_tryon_cache_key
from fashx.tryon.idempotency import compute_request_hash
from fashx.tryon.ports import TryOnModelAdapterPort
from fashx.tryon.repositories.tryon_repository import TryOnUnitOfWork
from fashx.tryon.validation.category_policy import (
    CategorySupportStatus,
    get_category_policy,
)


@dataclass(frozen=True)
class AcceptTryOnCommand:
    user_id: UUID
    product_id: UUID
    offer_id: UUID | None
    shopper_asset_id: UUID
    garment_asset_id: UUID | None
    idempotency_key: str
    render_config: dict[str, Any] | None = None


@dataclass(frozen=True)
class AcceptTryOnResult:
    job_id: UUID
    status: str
    progress_stage: str
    reused: bool
    is_cached: bool
    status_url: str
    result_url: str | None = None


class AcceptTryOnJobUseCase:
    """Accepts and validates a shopper's VTO request, enforcing strict ownership, DPDP consent,

    canonical idempotency hashing, cache eligibility, and transactional outbox dispatch.
    """

    def __init__(
        self,
        tryon_uow: TryOnUnitOfWork,
        profile_uow: ProfileUnitOfWork,
        catalog_uow: CatalogUnitOfWork,
        adapter: TryOnModelAdapterPort | None = None,
        validation_service: Any | None = None,
        *,
        model_version: str | None = None,
        pipeline_version: str | None = None,
        validation_policy_version: str = "v1.0",
    ) -> None:
        self.tryon_uow = tryon_uow
        self.profile_uow = profile_uow
        self.catalog_uow = catalog_uow
        self.validation_service = validation_service
        self.validation_policy_version = validation_policy_version

        if adapter is not None:
            self.adapter = adapter
            self.model_version = model_version or getattr(adapter, "model_version", "tryon-v1.6")
            self.pipeline_version = pipeline_version or getattr(adapter, "pipeline_version", "pilot-pipe-v1")
        else:
            from fashx.core.dependencies import get_tryon_adapter

            self.adapter = get_tryon_adapter()
            self.model_version = model_version or getattr(self.adapter, "model_version", "tryon-v1.6")
            self.pipeline_version = pipeline_version or getattr(self.adapter, "pipeline_version", "pilot-pipe-v1")

    async def execute(self, cmd: AcceptTryOnCommand) -> AcceptTryOnResult:
        settings = get_settings()

        # 1. User & Explicit Purpose-Bound DPDP Consent Verification
        async with self.profile_uow:
            user = await self.profile_uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

            # Check explicit THIRD_PARTY_VTO_PROCESSING consent (with fallback to body_photo)
            has_vto_consent = await self.profile_uow.consents.has_consent(
                cmd.user_id, "THIRD_PARTY_VTO_PROCESSING"
            )
            if not has_vto_consent:
                has_vto_consent = await self.profile_uow.consents.has_consent(
                    cmd.user_id, "body_photo"
                )
            if not has_vto_consent:
                raise ApiError(
                    403,
                    "VTO_CONSENT_REQUIRED",
                    "Shopper has not granted consent for virtual try-on processing.",
                )

            # 2. Portrait Photo Ownership & Anti-Enumeration Verification
            photo = await self.profile_uow.photos.get_owned(cmd.shopper_asset_id, cmd.user_id)
            if photo is None:
                # Anti-enumeration: Return 404 whether non-existent or owned by another user
                raise ApiError(
                    404,
                    "IMAGE_NOT_OWNED_OR_NOT_FOUND",
                    "Shopper photograph asset not found or not owned by user.",
                )

            if getattr(photo, "status", "accepted") != "accepted":
                raise ValidationError(
                    f"User portrait photo status is '{photo.status}'; must be 'accepted' to run try-on.",
                    field="shopper_asset_id",
                )

            photo_id = photo.id
            photo_version = getattr(photo, "version", 1)
            photo_hash = getattr(photo, "content_sha256", None) or photo.storage_key

        # 3. Garment Eligibility, Category Policy & Merchant Licensing
        async with self.catalog_uow:
            garment = await self.catalog_uow.canonical_garments.get_by_id(cmd.product_id)
            if garment is None:
                raise EntityNotFoundError("CanonicalGarment", cmd.product_id)

            # Category policy evaluation
            policy = get_category_policy(garment.category)
            if policy.status == CategorySupportStatus.UNSUPPORTED:
                raise ApiError(
                    422,
                    "UNSUPPORTED_GARMENT_CATEGORY",
                    f"Virtual try-on is not supported for category '{garment.category}'.",
                )
            if policy.status == CategorySupportStatus.PENDING:
                raise ApiError(
                    422,
                    "UNSUPPORTED_GARMENT_CATEGORY",
                    f"Virtual try-on for ethnic drape category '{garment.category}' is pending visual evaluation.",
                )

            # Product status check
            if getattr(garment, "tryon_supported", True) is False:
                raise ApiError(
                    422,
                    "UNSUPPORTED_GARMENT",
                    "Virtual try-on is disabled for this product.",
                )

            # Merchant permission verification
            if hasattr(self.catalog_uow, "merchant_products") and hasattr(self.catalog_uow, "sources"):
                products = await self.catalog_uow.merchant_products.get_by_canonical_garment_id(garment.id)
                if products:
                    for prod in products:
                        if prod.source_id:
                            src = await self.catalog_uow.sources.get_by_id(prod.source_id)
                            if src and (src.status != "cleared" or not src.rights_tryon):
                                raise ApiError(
                                    422,
                                    "GARMENT_PROCESSING_NOT_AUTHORIZED",
                                    "Merchant license does not permit virtual try-on processing.",
                                )

            garment_id = garment.id
            garment_version = garment.version

        # 4. Canonical Request Hashing (Rule 7.4.9)
        provider_name = getattr(self.adapter, "provider", "fashn_api")
        request_hash = compute_request_hash(
            user_id=cmd.user_id,
            product_id=garment_id,
            offer_id=cmd.offer_id,
            shopper_asset_id=photo_id,
            garment_asset_id=cmd.garment_asset_id,
            shopper_asset_version=photo_version,
            garment_asset_version=garment_version,
            provider=provider_name,
            model_version=self.model_version,
            validation_policy_version=self.validation_policy_version,
        )

        # 5. Composite Cache Key (Rule 7.4.10)
        artifact_key = compute_tryon_cache_key(
            user_photo_hash=photo_hash,
            garment_id=garment_id,
            garment_version=garment_version,
            model_version=self.model_version,
            pipeline_version=self.pipeline_version,
            render_config=cmd.render_config,
        )

        async with self.tryon_uow:
            # 6. Idempotency Key & Request Hash Conflict Check (Rule 7.4.9)
            existing_job = await self.tryon_uow.jobs.get_by_user_and_idempotency(
                cmd.user_id, cmd.idempotency_key
            )
            if existing_job is not None:
                # Compare canonical request hashes
                if existing_job.request_hash and existing_job.request_hash != request_hash:
                    raise ApiError(
                        409,
                        "IDEMPOTENCY_CONFLICT",
                        "Idempotency-Key was previously used with a different request payload.",
                    )

                artifact = await self.tryon_uow.artifacts.get_by_artifact_key(existing_job.artifact_key)
                return AcceptTryOnResult(
                    job_id=existing_job.id,
                    status=existing_job.status,
                    progress_stage=getattr(existing_job, "progress_stage", None) or "waiting_for_worker",
                    reused=True,
                    is_cached=existing_job.status == "completed",
                    status_url=f"/api/v1/tryon/jobs/{existing_job.id}",
                    result_url=artifact.result_key if artifact else None,
                )

            # 7. Check Reusable Result Eligibility (Rule 7.4.10)
            cached_artifact = await self.tryon_uow.artifacts.get_by_artifact_key(artifact_key)
            if cached_artifact is not None:
                # Verify that cached job belongs to the same user or user has valid consent
                cached_job = await self.tryon_uow.jobs.get_by_id(cached_artifact.job_id)
                if cached_job is not None and cached_job.user_id == cmd.user_id:
                    return AcceptTryOnResult(
                        job_id=cached_artifact.job_id,
                        status="completed",
                        progress_stage="completed",
                        reused=True,
                        is_cached=True,
                        status_url=f"/api/v1/tryon/jobs/{cached_artifact.job_id}",
                        result_url=cached_artifact.result_key,
                    )

            # 8. Budget and Daily Cap Protection
            from fashx.ml.breaker import check_daily_budget_exceeded, check_user_daily_cap_exceeded

            if hasattr(self.tryon_uow, "session") and self.tryon_uow.session:
                if await check_daily_budget_exceeded(self.tryon_uow.session, settings.tryon_daily_budget_usd):
                    raise ApiError(503, "SERVICE_UNAVAILABLE", "Try-on inference is at daily capacity.")
                if await check_user_daily_cap_exceeded(
                    self.tryon_uow.session, cmd.user_id, settings.tryon_user_daily_cap
                ):
                    raise ApiError(429, "RATE_LIMIT_EXCEEDED", "Daily try-on cap exceeded.")

            # 9. Transactional Job & Outbox Persistence (Rule 7.4.11 & 7.4.12)
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
                    provider=provider_name,
                    request_hash=request_hash,
                    validation_policy_version=self.validation_policy_version,
                    progress_stage="waiting_for_worker",
                )

                # Persist Outbox event in the same atomic transaction
                if hasattr(self.tryon_uow, "session") and self.tryon_uow.session:
                    outbox = SqlOutboxRepository(self.tryon_uow.session)
                    await outbox.add(
                        message="vto.job.queued",
                        payload={"job_id": str(job.id), "user_id": str(cmd.user_id)},
                    )

                await self.tryon_uow.commit()

            except IntegrityError:
                await self.tryon_uow.rollback()
                winning_job = await self.tryon_uow.jobs.get_by_user_and_idempotency(
                    cmd.user_id, cmd.idempotency_key
                )
                if winning_job is not None:
                    if winning_job.request_hash and winning_job.request_hash != request_hash:
                        raise ApiError(
                            409,
                            "IDEMPOTENCY_CONFLICT",
                            "Idempotency-Key was previously used with a different request payload.",
                        )
                    artifact = await self.tryon_uow.artifacts.get_by_artifact_key(winning_job.artifact_key)
                    return AcceptTryOnResult(
                        job_id=winning_job.id,
                        status=winning_job.status,
                        progress_stage=getattr(winning_job, "progress_stage", None) or "waiting_for_worker",
                        reused=True,
                        is_cached=winning_job.status == "completed",
                        status_url=f"/api/v1/tryon/jobs/{winning_job.id}",
                        result_url=artifact.result_key if artifact else None,
                    )
                raise

        return AcceptTryOnResult(
            job_id=job.id,
            status="queued",
            progress_stage="waiting_for_worker",
            reused=False,
            is_cached=False,
            status_url=f"/api/v1/tryon/jobs/{job.id}",
            result_url=None,
        )
