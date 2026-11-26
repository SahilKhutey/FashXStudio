"""Orchestration service for Shopper Fit Profile (Phase 08.2).

Guarantees:
1. Authenticated shopper ownership enforced on every operation.
2. Measurements are strictly stored as measurement_subject=BODY and never overwrite merchant charts.
3. Explicit FIT_PROFILE_STORAGE consent enforced before recording measurements.
4. Measurement values are never written to application logs or audit payloads.
5. Virtual try-on outputs are rejected as measurement evidence.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fashx.profile.consent import FitConsentService
from fashx.profile.fit_policy import (
    evaluate_all_categories_readiness,
    evaluate_category_readiness,
    get_category_policy,
)
from fashx.profile.fit_schemas import (
    CategoryFitPreferenceItem,
    CategoryReadinessItem,
    ConsentPurpose,
    FitConsentStatusResponse,
    FitPreference,
    FitProfileResponse,
    MeasurementBatchRequest,
    MeasurementDefinitionResponse,
    MeasurementHistoryItem,
    MeasurementMethod,
    MeasurementSource,
    MeasurementStatus,
    MeasurementSubject,
    MeasurementUpdateRequest,
    ShopperMeasurementResponse,
)
from fashx.profile.measurement_definitions import list_measurement_definitions
from fashx.profile.preferences import (
    validate_category,
    validate_fit_preference,
)
from fashx.profile.repositories.fit_profile_repository import FitProfileRepository
from fashx.profile.units import ProfileUnit
from fashx.profile.validation import (
    MeasurementValidationOutcome,
    MeasurementValidationStatus,
    evaluate_measurement_freshness,
    validate_measurement,
)

logger = logging.getLogger(__name__)


class VtoMeasurementEvidenceError(ValueError):
    """Raised if a VTO output or render is supplied as evidence to update shopper measurements."""


class FitProfileService:
    """High-level service coordinating fit profiles, measurements, consent, and preferences."""

    def __init__(
        self,
        repository: FitProfileRepository | None = None,
        consent_service: FitConsentService | None = None,
    ) -> None:
        self.repo = repository or FitProfileRepository()
        self.consent = consent_service or FitConsentService()

    @staticmethod
    def reject_vto_as_measurement_evidence(source_or_payload: str) -> None:
        """Invariant: VTO outputs must never be used to update shopper measurements."""
        norm = str(source_or_payload).strip().upper()
        if any(tag in norm for tag in ("VTO", "TRYON", "TRY_ON", "GENERATED_IMAGE")):
            raise VtoMeasurementEvidenceError(
                "VTO output cannot be used as evidence to populate or update body measurements."
            )

    def _to_measurement_response(
        self, rec: Any, validation_message: str | None = None
    ) -> ShopperMeasurementResponse:
        freshness_anchor = rec.verified_at or rec.measured_at
        needs_confirm, fresh_status = evaluate_measurement_freshness(
            freshness_anchor, rec.updated_at
        )
        effective_status = rec.status
        if rec.status == "PROVIDED" and needs_confirm:
            effective_status = fresh_status

        orig_val = (
            Decimal(str(rec.original_value))
            if rec.original_value is not None
            else Decimal(str(rec.value_cm))
        )
        norm_val = (
            Decimal(str(rec.normalized_value))
            if rec.normalized_value is not None
            else Decimal(str(rec.value_cm))
        )

        return ShopperMeasurementResponse(
            id=rec.id,
            field=rec.measurement_type,
            measurement_subject=MeasurementSubject.BODY,
            value=orig_val,
            unit=ProfileUnit(rec.original_unit or "CM"),
            normalized_value=norm_val,
            normalized_unit=ProfileUnit(rec.normalized_unit or "CM"),
            source=MeasurementSource(
                rec.source if rec.source in ("MANUAL", "IMPORTED") else "MANUAL"
            ),
            measurement_method=MeasurementMethod(rec.measurement_method or "SELF_MEASURED"),
            status=MeasurementStatus(effective_status),
            validation_status=MeasurementValidationStatus(rec.validation_status or "ACCEPTED"),
            validation_message=validation_message,
            policy_version=rec.policy_version or "1.0",
            schema_version=rec.schema_version or "1.0",
            measured_at=rec.measured_at or rec.recorded_at or rec.created_at,
            created_at=rec.created_at or rec.recorded_at,
            updated_at=rec.updated_at or rec.recorded_at,
            verified_at=rec.verified_at,
            expires_at=rec.expires_at,
            needs_confirmation=needs_confirm
            or (rec.validation_status == MeasurementValidationStatus.NEEDS_CONFIRMATION.value),
            version=rec.version or 1,
        )

    async def get_profile(self, user_id: UUID) -> FitProfileResponse:
        """Retrieve authenticated shopper's fit profile and category readiness."""
        profile = await self.repo.get_or_create_profile(user_id)
        measurements_rows = await self.repo.list_measurements(user_id)
        cat_pref_rows = await self.repo.list_category_preferences(user_id)
        consents = await self.consent.get_all_consents(user_id)

        measurements_resp = [self._to_measurement_response(m) for m in measurements_rows]
        provided_fields = {
            m.field
            for m in measurements_resp
            if m.status not in (MeasurementStatus.WITHDRAWN, MeasurementStatus.NOT_PROVIDED)
        }
        readiness_map = evaluate_all_categories_readiness(provided_fields)
        readiness_resp = {
            cat: CategoryReadinessItem(
                category=r.category,
                status=r.status,
                policy_version=r.policy_version,
                required_fields=list(r.required_fields),
                optional_fields=list(r.optional_fields),
                missing_fields=list(r.missing_fields),
                message=r.message,
            )
            for cat, r in readiness_map.items()
        }

        has_any_ready = any(r.status == "READY" for r in readiness_map.values())
        overall_status = "PROFILE_READY" if has_any_ready else "PROFILE_INCOMPLETE"

        pref_val = profile.preferred_fit or FitPreference.NO_PREFERENCE.value
        try:
            default_pref_enum = FitPreference(pref_val)
        except ValueError:
            default_pref_enum = FitPreference.NO_PREFERENCE

        unit_val = getattr(profile, "preferred_measurement_unit", "CM") or "CM"
        return FitProfileResponse(
            status=overall_status,
            profile_id=str(profile.id),
            schema_version="1.0",
            preferred_unit=ProfileUnit(unit_val),
            default_fit_preference=default_pref_enum,
            preference_updated_at=profile.updated_at,
            measurements=measurements_resp,
            category_preferences=[
                CategoryFitPreferenceItem(
                    category=cp.category,
                    fit_preference=FitPreference(cp.fit_preference),
                    updated_at=cp.updated_at,
                )
                for cp in cat_pref_rows
            ],
            category_readiness=readiness_resp,
            consents=consents,
            version=profile.version,
        )

    async def add_measurements(
        self,
        *,
        user_id: UUID,
        batch: MeasurementBatchRequest,
        source: str = "MANUAL",
    ) -> FitProfileResponse:
        """All-or-nothing batch entry of shopper body measurements requiring FIT_PROFILE_STORAGE consent."""
        self.reject_vto_as_measurement_evidence(source)
        await self.consent.require_storage_consent(user_id)

        # Validate ALL items in batch BEFORE persisting any (all-or-nothing invariant)
        validated: list[tuple[Any, MeasurementValidationOutcome]] = []
        for item in batch.measurements:
            outcome = validate_measurement(
                item.field,
                item.value,
                item.unit,
                confirm_unusual=item.confirm_unusual,
            )
            validated.append((item, outcome))

        for item, outcome in validated:
            status_val = (
                "NEEDS_REVIEW"
                if outcome.validation_status == MeasurementValidationStatus.NEEDS_CONFIRMATION
                else "PROVIDED"
            )
            await self.repo.upsert_measurement(
                user_id=user_id,
                field_code=outcome.field,
                original_value=item.value,
                original_unit=item.unit.value,
                normalized_value=outcome.normalized_value,
                normalized_unit=outcome.normalized_unit.value,
                source="MANUAL",
                measurement_method=item.measurement_method.value,
                status=status_val,
                validation_status=outcome.validation_status.value,
                policy_version=outcome.policy_version,
                measured_at=item.measured_at,
                change_source="SHOPPER_MANUAL_ENTRY",
            )
            # Log ONLY field identifier — NEVER numeric values
            await self.repo.log_audit_event(
                user_id=user_id,
                event_type="MEASUREMENT_SAVED",
                actor_id=str(user_id),
                field_code=outcome.field,
            )
            logger.info("fit_profile.measurement_saved field=%s", outcome.field)

        await self.repo.invalidate_fit_recommendations(user_id)
        return await self.get_profile(user_id)

    async def update_measurement(
        self,
        *,
        user_id: UUID,
        field: str,
        payload: MeasurementUpdateRequest,
    ) -> ShopperMeasurementResponse:
        """Update an existing measurement with optimistic concurrency and history preservation."""
        await self.consent.require_storage_consent(user_id)
        outcome = validate_measurement(
            field,
            payload.value,
            payload.unit,
            confirm_unusual=payload.confirm_unusual,
        )
        status_val = (
            "NEEDS_REVIEW"
            if outcome.validation_status == MeasurementValidationStatus.NEEDS_CONFIRMATION
            else "PROVIDED"
        )
        updated = await self.repo.update_measurement_with_version(
            user_id=user_id,
            field_code=outcome.field,
            expected_version=payload.expected_version,
            original_value=payload.value,
            original_unit=payload.unit.value,
            normalized_value=outcome.normalized_value,
            normalized_unit=outcome.normalized_unit.value,
            measurement_method=payload.measurement_method.value,
            status=status_val,
            validation_status=outcome.validation_status.value,
            policy_version=outcome.policy_version,
            measured_at=payload.measured_at,
            change_source="SHOPPER_UPDATE",
        )
        await self.repo.invalidate_fit_recommendations(user_id)
        await self.repo.log_audit_event(
            user_id=user_id,
            event_type="MEASUREMENT_UPDATED",
            actor_id=str(user_id),
            field_code=outcome.field,
        )
        logger.info("fit_profile.measurement_updated field=%s", outcome.field)
        return self._to_measurement_response(updated, validation_message=outcome.message)

    async def confirm_measurement(self, user_id: UUID, field: str) -> ShopperMeasurementResponse:
        """Confirm an aged or unusual measurement remains accurate."""
        await self.consent.require_storage_consent(user_id)
        rec = await self.repo.confirm_measurement(user_id, field)
        await self.repo.invalidate_fit_recommendations(user_id)
        await self.repo.log_audit_event(
            user_id=user_id,
            event_type="MEASUREMENT_CONFIRMED",
            actor_id=str(user_id),
            field_code=rec.measurement_type,
        )
        return self._to_measurement_response(rec)

    async def delete_measurement(self, user_id: UUID, field: str) -> bool:
        """Delete a measurement from the shopper's active fit profile."""
        deleted = await self.repo.delete_measurement(user_id, field)
        if deleted:
            await self.repo.invalidate_fit_recommendations(user_id)
            await self.repo.log_audit_event(
                user_id=user_id,
                event_type="MEASUREMENT_DELETED",
                actor_id=str(user_id),
                field_code=field.strip().upper(),
            )
            logger.info("fit_profile.measurement_deleted field=%s", field.strip().upper())
        return deleted

    async def get_history(
        self, user_id: UUID, field: str | None = None
    ) -> list[MeasurementHistoryItem]:
        """Retrieve owner-scoped measurement history."""
        rows = await self.repo.list_history(user_id, field)
        return [
            MeasurementHistoryItem(
                id=r.id,
                measurement_id=r.measurement_id,
                field=r.field_code,
                previous_value=Decimal(str(r.previous_value))
                if r.previous_value is not None
                else None,
                previous_unit=ProfileUnit(r.previous_unit) if r.previous_unit else None,
                new_value=Decimal(str(r.new_value)) if r.new_value is not None else None,
                new_unit=ProfileUnit(r.new_unit) if r.new_unit else None,
                normalized_value=Decimal(str(r.normalized_value))
                if r.normalized_value is not None
                else None,
                change_source=r.change_source,
                changed_at=r.changed_at,
            )
            for r in rows
        ]

    async def update_default_preference(
        self,
        *,
        user_id: UUID,
        default_fit_preference: FitPreference,
        preferred_unit: ProfileUnit | None = None,
    ) -> FitProfileResponse:
        """Update subjective default fit preference without altering measurements or charts."""
        norm_pref = validate_fit_preference(default_fit_preference.value)
        await self.repo.update_default_preference(
            user_id,
            default_fit_preference=norm_pref,
            preferred_unit=preferred_unit.value if preferred_unit else None,
        )
        await self.repo.log_audit_event(
            user_id=user_id,
            event_type="DEFAULT_FIT_PREFERENCE_UPDATED",
            actor_id=str(user_id),
        )
        return await self.get_profile(user_id)

    async def update_category_preference(
        self,
        *,
        user_id: UUID,
        category: str,
        fit_preference: FitPreference,
    ) -> CategoryFitPreferenceItem:
        """Update independent fit preference for a supported garment category."""
        norm_cat = validate_category(category)
        norm_pref = validate_fit_preference(fit_preference.value)
        rec = await self.repo.upsert_category_preference(user_id, norm_cat, norm_pref)
        await self.repo.log_audit_event(
            user_id=user_id,
            event_type="CATEGORY_FIT_PREFERENCE_UPDATED",
            actor_id=str(user_id),
            category=norm_cat,
        )
        return CategoryFitPreferenceItem(
            category=rec.category,
            fit_preference=FitPreference(rec.fit_preference),
            updated_at=rec.updated_at or datetime.now(UTC),
        )

    async def delete_category_preference(self, user_id: UUID, category: str) -> bool:
        """Remove subjective fit preference for one category without affecting others."""
        norm_cat = validate_category(category)
        deleted = await self.repo.delete_category_preference(user_id, norm_cat)
        if deleted:
            await self.repo.log_audit_event(
                user_id=user_id,
                event_type="CATEGORY_FIT_PREFERENCE_CLEARED",
                actor_id=str(user_id),
                category=norm_cat,
            )
        return deleted

    async def get_category_policy_readiness(
        self, user_id: UUID, category: str
    ) -> CategoryReadinessItem:
        """Return category-specific required/optional guidance and missing fields."""
        get_category_policy(category)
        measurements = await self.repo.list_measurements(user_id)
        provided_fields = {
            m.measurement_type
            for m in measurements
            if m.status not in (MeasurementStatus.WITHDRAWN.value, MeasurementStatus.NOT_PROVIDED.value)
        }
        readiness = evaluate_category_readiness(category, provided_fields)
        return CategoryReadinessItem(
            category=readiness.category,
            status=readiness.status,
            policy_version=readiness.policy_version,
            required_fields=list(readiness.required_fields),
            optional_fields=list(readiness.optional_fields),
            missing_fields=list(readiness.missing_fields),
            message=readiness.message,
        )

    @staticmethod
    def list_measurement_definitions() -> list[MeasurementDefinitionResponse]:
        """Return measurement explanations, tape positioning, and supported categories."""
        return [
            MeasurementDefinitionResponse(
                code=d.code,
                display_name=d.display_name,
                explanation=d.explanation,
                tape_positioning=d.tape_positioning,
                how_to_hold=d.how_to_hold,
                example_input=d.example_input,
                measurement_type=d.measurement_type,
                supported_categories=list(d.supported_categories),
                default_unit=d.default_unit,
                is_optional_contextual=d.is_optional_contextual,
            )
            for d in list_measurement_definitions()
        ]

    async def get_consent_status(self, user_id: UUID) -> FitConsentStatusResponse:
        consents = await self.consent.get_all_consents(user_id)
        return FitConsentStatusResponse(**consents)

    async def update_consent(
        self,
        *,
        user_id: UUID,
        purpose: ConsentPurpose,
        granted: bool,
        is_18_or_older: bool | None = None,
        consent_version: str = "2026.1",
    ) -> FitConsentStatusResponse:
        """Grant or withdraw purpose-specific fit profile consent with immediate enforcement."""
        await self.consent.set_consent(
            user_id=user_id,
            purpose=purpose,
            granted=granted,
            is_18_or_older=is_18_or_older,
            consent_version=consent_version,
        )
        if not granted:
            await self.repo.invalidate_fit_recommendations(user_id)
            if purpose == ConsentPurpose.FIT_PROFILE_STORAGE:
                await self.repo.mark_measurements_withdrawn(user_id)
            await self.repo.log_audit_event(
                user_id=user_id,
                event_type=f"CONSENT_WITHDRAWN:{purpose.value}",
                actor_id=str(user_id),
            )
        else:
            await self.repo.log_audit_event(
                user_id=user_id,
                event_type=f"CONSENT_GRANTED:{purpose.value}",
                actor_id=str(user_id),
            )

        return await self.get_consent_status(user_id)

    async def delete_fit_profile(self, user_id: UUID) -> dict[str, int]:
        """Delete fit profile measurements, history, and revoke storage/recommendation consents."""
        counts = await self.repo.delete_fit_profile(user_id)
        for purpose in (
            ConsentPurpose.FIT_PROFILE_STORAGE,
            ConsentPurpose.FIT_RECOMMENDATION_PROCESSING,
            ConsentPurpose.THIRD_PARTY_FIT_PROCESSING,
            ConsentPurpose.MODEL_TRAINING,
        ):
            if await self.consent.has_consent(user_id, purpose):
                await self.consent.set_consent(
                    user_id=user_id,
                    purpose=purpose,
                    granted=False,
                    decision_source="fit_profile_deletion",
                )
        logger.info("fit_profile.deleted")
        return counts
