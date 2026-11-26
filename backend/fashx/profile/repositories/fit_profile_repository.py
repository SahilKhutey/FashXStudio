"""Transactional repository for Shopper Fit Profile, measurements, history, and preferences (Phase 08.2)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.profile import (
    CategoryFitPreference,
    ProfileAuditEvent,
    ProfileMeasurement,
    ProfileMeasurementHistory,
    ShopperProfile,
)
from database.models.tryon import FitRecommendation


class OptimisticLockConflictError(RuntimeError):
    """Raised when a stale measurement version attempts to overwrite newer state."""


class FitProfileRepository:
    """Owner-scoped repository for fit profiles, body measurements, history, and preferences."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session
        # In-memory fallback stores for sandbox / zero-DB unit tests
        self._mem_profiles: dict[UUID, ShopperProfile] = {}
        self._mem_measurements: dict[tuple[UUID, str], ProfileMeasurement] = {}
        self._mem_history: list[ProfileMeasurementHistory] = []
        self._mem_cat_prefs: dict[tuple[UUID, str], CategoryFitPreference] = {}
        self._mem_audit_events: list[ProfileAuditEvent] = []
        self._invalidated_users: list[UUID] = []

    async def get_or_create_profile(self, user_id: UUID) -> ShopperProfile:
        """Fetch owner-scoped ShopperProfile or initialize empty profile with NO_PREFERENCE."""
        if self._session is not None:
            stmt = select(ShopperProfile).where(ShopperProfile.user_id == user_id)
            res = await self._session.execute(stmt)
            prof = res.scalar_one_or_none()
            if prof is not None:
                return prof

            now = datetime.now(UTC)
            prof = ShopperProfile(
                id=uuid4(),
                user_id=user_id,
                preferred_measurement_unit="CM",
                preferred_fit="NO_PREFERENCE",
                style_preferences=[],
                preferred_colors=[],
                product_categories=[],
                shopping_preferences={},
                version=1,
                created_at=now,
                updated_at=now,
            )
            self._session.add(prof)
            await self._session.flush()
            return prof

        prof = self._mem_profiles.get(user_id)
        if prof is not None:
            return prof
        now = datetime.now(UTC)
        prof = ShopperProfile(
            id=uuid4(),
            user_id=user_id,
            preferred_measurement_unit="CM",
            preferred_fit="NO_PREFERENCE",
            style_preferences=[],
            preferred_colors=[],
            product_categories=[],
            shopping_preferences={},
            version=1,
            created_at=now,
            updated_at=now,
        )
        self._mem_profiles[user_id] = prof
        return prof

    async def update_default_preference(
        self,
        user_id: UUID,
        *,
        default_fit_preference: str,
        preferred_unit: str | None = None,
    ) -> ShopperProfile:
        """Persist subjective default fit preference and/or preferred display unit."""
        prof = await self.get_or_create_profile(user_id)
        now = datetime.now(UTC)
        if self._session is not None:
            vals: dict[str, Any] = {
                "preferred_fit": default_fit_preference,
                "updated_at": now,
                "version": ShopperProfile.version + 1,
            }
            if preferred_unit is not None:
                vals["preferred_measurement_unit"] = preferred_unit
            stmt = (
                update(ShopperProfile)
                .where(ShopperProfile.id == prof.id, ShopperProfile.user_id == user_id)
                .values(**vals)
            )
            await self._session.execute(stmt)
            await self._session.flush()
            prof.preferred_fit = default_fit_preference
            if preferred_unit is not None:
                prof.preferred_measurement_unit = preferred_unit
            prof.updated_at = now
            prof.version += 1
            return prof

        prof.preferred_fit = default_fit_preference
        if preferred_unit is not None:
            prof.preferred_measurement_unit = preferred_unit
        prof.updated_at = now
        prof.version += 1
        return prof

    async def list_measurements(self, user_id: UUID) -> list[ProfileMeasurement]:
        """List all body measurements owned strictly by `user_id`."""
        if self._session is not None:
            stmt = (
                select(ProfileMeasurement)
                .where(ProfileMeasurement.user_id == user_id)
                .order_by(ProfileMeasurement.measurement_type)
            )
            res = await self._session.execute(stmt)
            return list(res.scalars().all())

        rows = [m for (uid, _), m in self._mem_measurements.items() if uid == user_id]
        rows.sort(key=lambda m: m.measurement_type)
        return rows

    async def get_measurement(self, user_id: UUID, field_code: str) -> ProfileMeasurement | None:
        """Fetch one owner-scoped measurement row by field code."""
        norm_field = field_code.strip().upper()
        if self._session is not None:
            stmt = select(ProfileMeasurement).where(
                ProfileMeasurement.user_id == user_id,
                ProfileMeasurement.measurement_type == norm_field,
            )
            res = await self._session.execute(stmt)
            return res.scalar_one_or_none()
        return self._mem_measurements.get((user_id, norm_field))

    async def upsert_measurement(
        self,
        *,
        user_id: UUID,
        field_code: str,
        original_value: Decimal,
        original_unit: str,
        normalized_value: Decimal,
        normalized_unit: str,
        source: str,
        measurement_method: str,
        status: str,
        validation_status: str,
        policy_version: str,
        measured_at: datetime | None,
        change_source: str = "SHOPPER_MANUAL_ENTRY",
    ) -> ProfileMeasurement:
        """Create or update a shopper's body measurement and append history."""
        norm_field = field_code.strip().upper()
        now = datetime.now(UTC)
        effective_measured_at = measured_at or now
        existing = await self.get_measurement(user_id, norm_field)

        if existing is None:
            rec = ProfileMeasurement(
                id=uuid4(),
                user_id=user_id,
                measurement_type=norm_field,
                measurement_subject="BODY",
                value_cm=float(normalized_value),
                original_value=float(original_value),
                original_unit=original_unit,
                normalized_value=float(normalized_value),
                normalized_unit=normalized_unit,
                source=source,
                measurement_method=measurement_method,
                status=status,
                validation_status=validation_status,
                policy_version=policy_version,
                schema_version="1.0",
                measured_at=effective_measured_at,
                recorded_at=now,
                created_at=now,
                updated_at=now,
                verified_at=None,
                version=1,
            )
            hist = ProfileMeasurementHistory(
                id=uuid4(),
                measurement_id=rec.id,
                user_id=user_id,
                field_code=norm_field,
                previous_value=None,
                previous_unit=None,
                new_value=float(original_value),
                new_unit=original_unit,
                normalized_value=float(normalized_value),
                change_source=change_source,
                changed_at=now,
            )
            if self._session is not None:
                self._session.add(rec)
                self._session.add(hist)
                await self._session.flush()
            else:
                self._mem_measurements[(user_id, norm_field)] = rec
                self._mem_history.append(hist)
            return rec

        return await self.update_measurement_with_version(
            user_id=user_id,
            field_code=norm_field,
            expected_version=existing.version,
            original_value=original_value,
            original_unit=original_unit,
            normalized_value=normalized_value,
            normalized_unit=normalized_unit,
            measurement_method=measurement_method,
            status=status,
            validation_status=validation_status,
            policy_version=policy_version,
            measured_at=effective_measured_at,
            change_source=change_source,
        )

    async def update_measurement_with_version(
        self,
        *,
        user_id: UUID,
        field_code: str,
        expected_version: int,
        original_value: Decimal,
        original_unit: str,
        normalized_value: Decimal,
        normalized_unit: str,
        measurement_method: str,
        status: str,
        validation_status: str,
        policy_version: str,
        measured_at: datetime | None,
        change_source: str = "SHOPPER_UPDATE",
    ) -> ProfileMeasurement:
        """Atomically update a measurement enforcing expected_version inside the transaction."""
        norm_field = field_code.strip().upper()
        current = await self.get_measurement(user_id, norm_field)
        if current is None:
            raise KeyError(f"Measurement '{norm_field}' does not exist for shopper")
        if current.version != expected_version:
            raise OptimisticLockConflictError(
                f"Measurement '{norm_field}' version mismatch: expected {expected_version}, found {current.version}"
            )

        now = datetime.now(UTC)
        effective_measured_at = measured_at or now
        prev_val = (
            float(current.original_value)
            if current.original_value is not None
            else float(current.value_cm)
        )
        prev_unit = current.original_unit or "CM"

        if self._session is not None:
            stmt = (
                update(ProfileMeasurement)
                .where(
                    ProfileMeasurement.id == current.id,
                    ProfileMeasurement.user_id == user_id,
                    ProfileMeasurement.version == expected_version,
                )
                .values(
                    value_cm=float(normalized_value),
                    original_value=float(original_value),
                    original_unit=original_unit,
                    normalized_value=float(normalized_value),
                    normalized_unit=normalized_unit,
                    measurement_method=measurement_method,
                    status=status,
                    validation_status=validation_status,
                    policy_version=policy_version,
                    measured_at=effective_measured_at,
                    updated_at=now,
                    version=ProfileMeasurement.version + 1,
                )
            )
            res = await self._session.execute(stmt)
            if res.rowcount != 1:
                raise OptimisticLockConflictError(
                    f"Concurrent update detected for measurement '{norm_field}'"
                )

            hist = ProfileMeasurementHistory(
                id=uuid4(),
                measurement_id=current.id,
                user_id=user_id,
                field_code=norm_field,
                previous_value=prev_val,
                previous_unit=prev_unit,
                new_value=float(original_value),
                new_unit=original_unit,
                normalized_value=float(normalized_value),
                change_source=change_source,
                changed_at=now,
            )
            self._session.add(hist)
            await self._session.flush()
            updated = await self.get_measurement(user_id, norm_field)
            assert updated is not None
            return updated

        # In-memory atomic update
        current.value_cm = float(normalized_value)
        current.original_value = float(original_value)
        current.original_unit = original_unit
        current.normalized_value = float(normalized_value)
        current.normalized_unit = normalized_unit
        current.measurement_method = measurement_method
        current.status = status
        current.validation_status = validation_status
        current.policy_version = policy_version
        current.measured_at = effective_measured_at
        current.updated_at = now
        current.version += 1

        self._mem_history.append(
            ProfileMeasurementHistory(
                id=uuid4(),
                measurement_id=current.id,
                user_id=user_id,
                field_code=norm_field,
                previous_value=prev_val,
                previous_unit=prev_unit,
                new_value=float(original_value),
                new_unit=original_unit,
                normalized_value=float(normalized_value),
                change_source=change_source,
                changed_at=now,
            )
        )
        return current

    async def confirm_measurement(self, user_id: UUID, field_code: str) -> ProfileMeasurement:
        """Confirm an existing or aged measurement remains current."""
        norm_field = field_code.strip().upper()
        current = await self.get_measurement(user_id, norm_field)
        if current is None:
            raise KeyError(f"Measurement '{norm_field}' does not exist for shopper")
        now = datetime.now(UTC)
        if self._session is not None:
            stmt = (
                update(ProfileMeasurement)
                .where(ProfileMeasurement.id == current.id, ProfileMeasurement.user_id == user_id)
                .values(
                    status="PROVIDED",
                    validation_status="ACCEPTED",
                    verified_at=now,
                    updated_at=now,
                    version=ProfileMeasurement.version + 1,
                )
            )
            await self._session.execute(stmt)
            await self._session.flush()
            updated = await self.get_measurement(user_id, norm_field)
            assert updated is not None
            return updated

        current.status = "PROVIDED"
        current.validation_status = "ACCEPTED"
        current.verified_at = now
        current.updated_at = now
        current.version += 1
        return current

    async def mark_measurements_withdrawn(self, user_id: UUID) -> int:
        """Mark stored measurements as WITHDRAWN when storage consent is revoked."""
        now = datetime.now(UTC)
        if self._session is not None:
            stmt = (
                update(ProfileMeasurement)
                .where(ProfileMeasurement.user_id == user_id)
                .values(status="WITHDRAWN", updated_at=now)
            )
            res = await self._session.execute(stmt)
            await self._session.flush()
            return int(res.rowcount or 0)

        count = 0
        for (uid, _), m in self._mem_measurements.items():
            if uid == user_id:
                m.status = "WITHDRAWN"
                m.updated_at = now
                count += 1
        return count

    async def delete_measurement(self, user_id: UUID, field_code: str) -> bool:
        """Delete a single measurement owned by `user_id`."""
        norm_field = field_code.strip().upper()
        current = await self.get_measurement(user_id, norm_field)
        if current is None:
            return False

        now = datetime.now(UTC)
        prev_val = (
            float(current.original_value)
            if current.original_value is not None
            else float(current.value_cm)
        )
        prev_unit = current.original_unit or "CM"
        hist = ProfileMeasurementHistory(
            id=uuid4(),
            measurement_id=current.id,
            user_id=user_id,
            field_code=norm_field,
            previous_value=prev_val,
            previous_unit=prev_unit,
            new_value=None,
            new_unit=None,
            normalized_value=None,
            change_source="SHOPPER_DELETE",
            changed_at=now,
        )

        if self._session is not None:
            await self._session.execute(
                delete(ProfileMeasurement).where(
                    ProfileMeasurement.id == current.id,
                    ProfileMeasurement.user_id == user_id,
                )
            )
            self._session.add(hist)
            await self._session.flush()
            return True

        del self._mem_measurements[(user_id, norm_field)]
        self._mem_history.append(hist)
        return True

    async def list_history(
        self, user_id: UUID, field_code: str | None = None
    ) -> list[ProfileMeasurementHistory]:
        """Return authorized measurement change history strictly scoped to `user_id`."""
        if self._session is not None:
            stmt = select(ProfileMeasurementHistory).where(
                ProfileMeasurementHistory.user_id == user_id
            )
            if field_code:
                stmt = stmt.where(
                    ProfileMeasurementHistory.field_code == field_code.strip().upper()
                )
            stmt = stmt.order_by(desc(ProfileMeasurementHistory.changed_at))
            res = await self._session.execute(stmt)
            return list(res.scalars().all())

        rows = [
            h
            for h in reversed(self._mem_history)
            if h.user_id == user_id
            and (field_code is None or h.field_code == field_code.strip().upper())
        ]
        rows.sort(key=lambda h: h.changed_at, reverse=True)
        return rows

    async def list_category_preferences(self, user_id: UUID) -> list[CategoryFitPreference]:
        """List independent category fit style preferences for `user_id`."""
        if self._session is not None:
            stmt = (
                select(CategoryFitPreference)
                .where(CategoryFitPreference.user_id == user_id)
                .order_by(CategoryFitPreference.category)
            )
            res = await self._session.execute(stmt)
            return list(res.scalars().all())

        rows = [p for (uid, _), p in self._mem_cat_prefs.items() if uid == user_id]
        rows.sort(key=lambda p: p.category)
        return rows

    async def upsert_category_preference(
        self, user_id: UUID, category: str, fit_preference: str
    ) -> CategoryFitPreference:
        """Create or update fit style preference for one garment category independently."""
        norm_cat = category.strip().upper()
        now = datetime.now(UTC)

        if self._session is not None:
            stmt = select(CategoryFitPreference).where(
                CategoryFitPreference.user_id == user_id,
                CategoryFitPreference.category == norm_cat,
            )
            res = await self._session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing is not None:
                existing.fit_preference = fit_preference
                existing.updated_at = now
                await self._session.flush()
                return existing

            rec = CategoryFitPreference(
                id=uuid4(),
                user_id=user_id,
                category=norm_cat,
                fit_preference=fit_preference,
                updated_at=now,
            )
            self._session.add(rec)
            await self._session.flush()
            return rec

        existing = self._mem_cat_prefs.get((user_id, norm_cat))
        if existing is not None:
            existing.fit_preference = fit_preference
            existing.updated_at = now
            return existing
        rec = CategoryFitPreference(
            id=uuid4(),
            user_id=user_id,
            category=norm_cat,
            fit_preference=fit_preference,
            updated_at=now,
        )
        self._mem_cat_prefs[(user_id, norm_cat)] = rec
        return rec

    async def delete_category_preference(self, user_id: UUID, category: str) -> bool:
        """Clear subjective preference for a single category without affecting others."""
        norm_cat = category.strip().upper()
        if self._session is not None:
            res = await self._session.execute(
                delete(CategoryFitPreference).where(
                    CategoryFitPreference.user_id == user_id,
                    CategoryFitPreference.category == norm_cat,
                )
            )
            await self._session.flush()
            return bool(res.rowcount and res.rowcount > 0)

        if (user_id, norm_cat) in self._mem_cat_prefs:
            del self._mem_cat_prefs[(user_id, norm_cat)]
            return True
        return False

    async def invalidate_fit_recommendations(self, user_id: UUID) -> int:
        """Invalidate prior fit recommendations whenever measurements or consent change."""
        self._invalidated_users.append(user_id)
        if self._session is not None:
            stmt = (
                update(FitRecommendation)
                .where(FitRecommendation.user_id == user_id, FitRecommendation.is_valid.is_(True))
                .values(is_valid=False)
            )
            res = await self._session.execute(stmt)
            await self._session.flush()
            return int(res.rowcount or 0)
        return 0

    async def log_audit_event(
        self,
        *,
        user_id: UUID,
        event_type: str,
        actor_id: str,
        field_code: str | None = None,
        category: str | None = None,
    ) -> None:
        """Record sanitized profile audit event (strictly no numeric measurement values)."""
        details: dict[str, Any] = {}
        if field_code:
            details["field"] = field_code
        if category:
            details["category"] = category

        evt = ProfileAuditEvent(
            id=uuid4(),
            user_id=user_id,
            event_type=event_type,
            actor_id=actor_id,
            details_json=details or None,
            created_at=datetime.now(UTC),
        )
        if self._session is not None:
            self._session.add(evt)
            await self._session.flush()
        else:
            self._mem_audit_events.append(evt)

    async def delete_fit_profile(self, user_id: UUID) -> dict[str, int]:
        """Delete fit profile measurements, history, and category preferences."""
        deleted_counts = {
            "measurements": 0,
            "history": 0,
            "category_preferences": 0,
        }

        if self._session is not None:
            res_m = await self._session.execute(
                delete(ProfileMeasurement).where(ProfileMeasurement.user_id == user_id)
            )
            res_h = await self._session.execute(
                delete(ProfileMeasurementHistory).where(
                    ProfileMeasurementHistory.user_id == user_id
                )
            )
            res_p = await self._session.execute(
                delete(CategoryFitPreference).where(CategoryFitPreference.user_id == user_id)
            )
            await self._session.execute(
                update(ShopperProfile)
                .where(ShopperProfile.user_id == user_id)
                .values(preferred_fit="NO_PREFERENCE", updated_at=datetime.now(UTC))
            )
            deleted_counts["measurements"] = int(res_m.rowcount or 0)
            deleted_counts["history"] = int(res_h.rowcount or 0)
            deleted_counts["category_preferences"] = int(res_p.rowcount or 0)
            await self.invalidate_fit_recommendations(user_id)
            await self.log_audit_event(
                user_id=user_id,
                event_type="FIT_PROFILE_DELETED",
                actor_id=str(user_id),
            )
            await self._session.flush()
            return deleted_counts

        m_keys = [k for k in self._mem_measurements if k[0] == user_id]
        for k in m_keys:
            del self._mem_measurements[k]
        deleted_counts["measurements"] = len(m_keys)

        before_h = len(self._mem_history)
        self._mem_history = [h for h in self._mem_history if h.user_id != user_id]
        deleted_counts["history"] = before_h - len(self._mem_history)

        p_keys = [k for k in self._mem_cat_prefs if k[0] == user_id]
        for k in p_keys:
            del self._mem_cat_prefs[k]
        deleted_counts["category_preferences"] = len(p_keys)

        if user_id in self._mem_profiles:
            self._mem_profiles[user_id].preferred_fit = "NO_PREFERENCE"

        await self.invalidate_fit_recommendations(user_id)
        await self.log_audit_event(
            user_id=user_id,
            event_type="FIT_PROFILE_DELETED",
            actor_id=str(user_id),
        )
        return deleted_counts
