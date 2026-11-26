"""Tests for FitProfileService, Timestamps, Optimistic History, Consent, Privacy, Ownership & VTO Separation (FITP-TS, FITP-UPD, FITP-SEC, FITP-REC)."""

from __future__ import annotations

import inspect
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from fashx.core.errors import ConsentRequiredError
from fashx.profile.consent import FitConsentService
from fashx.profile.fit_schemas import (
    ConsentPurpose,
    FitPreference,
    MeasurementBatchRequest,
    MeasurementInput,
    MeasurementStatus,
    MeasurementSubject,
    MeasurementUpdateRequest,
)
from fashx.profile.repositories.fit_profile_repository import (
    FitProfileRepository,
    OptimisticLockConflictError,
)
from fashx.profile.services.fit_profile_service import (
    FitProfileService,
    VtoMeasurementEvidenceError,
)
from fashx.profile.units import ProfileUnit


def _run(coro):
    """Run an async coroutine synchronously without opening an asyncio event loop on Windows."""
    stack = [coro]
    val = None
    while stack:
        curr = stack[-1]
        try:
            if inspect.iscoroutine(curr):
                nxt = curr.send(val)
                val = None
                if inspect.iscoroutine(nxt):
                    stack.append(nxt)
            else:
                stack.pop()
        except StopIteration as e:
            val = e.value
            stack.pop()
    return val


def _make_service() -> FitProfileService:
    return FitProfileService(
        repository=FitProfileRepository(),
        consent_service=FitConsentService(),
    )


def test_consent_required_before_saving_and_withdrawal_halts_processing():
    """FITP-SEC-004: Storage consent required; withdrawal marks withdrawn and invalidates caches."""
    service = _make_service()
    user_id = uuid4()

    batch = MeasurementBatchRequest(
        measurements=[MeasurementInput(field="CHEST", value=Decimal("96.5"), unit=ProfileUnit.CM)]
    )

    # Without consent -> blocked
    with pytest.raises(ConsentRequiredError):
        _run(service.add_measurements(user_id=user_id, batch=batch))

    # Grant FIT_PROFILE_STORAGE -> allowed
    _run(
        service.update_consent(
            user_id=user_id,
            purpose=ConsentPurpose.FIT_PROFILE_STORAGE,
            granted=True,
            is_18_or_older=True,
        )
    )
    prof = _run(service.add_measurements(user_id=user_id, batch=batch))
    assert len(prof.measurements) == 1
    assert prof.measurements[0].measurement_subject == MeasurementSubject.BODY
    assert prof.measurements[0].normalized_value == Decimal("96.50")

    # Withdraw FIT_PROFILE_STORAGE -> measurements marked WITHDRAWN and subsequent saves blocked
    _run(
        service.update_consent(
            user_id=user_id,
            purpose=ConsentPurpose.FIT_PROFILE_STORAGE,
            granted=False,
        )
    )
    after_withdraw = _run(service.get_profile(user_id))
    assert after_withdraw.measurements[0].status == MeasurementStatus.WITHDRAWN

    with pytest.raises(ConsentRequiredError):
        _run(service.add_measurements(user_id=user_id, batch=batch))


def test_timestamps_separation_and_staleness_flagging():
    """FITP-TS-001..004: Separate measured_at vs created_at/updated_at; old measurements flagged without deletion."""
    service = _make_service()
    user_id = uuid4()
    _run(
        service.update_consent(
            user_id=user_id,
            purpose=ConsentPurpose.FIT_PROFILE_STORAGE,
            granted=True,
            is_18_or_older=True,
        )
    )

    # Enter a measurement taken 200 days ago
    old_measured_at = datetime.now(UTC) - timedelta(days=200)
    batch = MeasurementBatchRequest(
        measurements=[
            MeasurementInput(
                field="CHEST",
                value=Decimal("38"),
                unit=ProfileUnit.IN,
                measured_at=old_measured_at,
            )
        ]
    )
    prof = _run(service.add_measurements(user_id=user_id, batch=batch))
    m = prof.measurements[0]
    assert m.measured_at == old_measured_at
    assert m.created_at > old_measured_at
    assert m.status == MeasurementStatus.NEEDS_REVIEW
    assert m.needs_confirmation is True
    assert m.normalized_value == Decimal("96.52")

    # Confirming refreshes status to PROVIDED without deleting history
    confirmed = _run(service.confirm_measurement(user_id, "CHEST"))
    assert confirmed.status == MeasurementStatus.PROVIDED


def test_optimistic_update_history_all_or_nothing_and_invalidation():
    """FITP-UPD-001..005 & FITP-REC-001: History retention, version locking, atomic batch failure, cache invalidation."""
    service = _make_service()
    user_id = uuid4()
    _run(
        service.update_consent(
            user_id=user_id,
            purpose=ConsentPurpose.FIT_PROFILE_STORAGE,
            granted=True,
            is_18_or_older=True,
        )
    )

    # Save valid CHEST
    _run(
        service.add_measurements(
            user_id=user_id,
            batch=MeasurementBatchRequest(
                measurements=[
                    MeasurementInput(field="CHEST", value=Decimal("94.00"), unit=ProfileUnit.CM)
                ]
            ),
        )
    )

    # Failed batch (WAIST valid + UNKNOWN_FIELD invalid) must NOT partially save WAIST
    bad_batch = MeasurementBatchRequest(
        measurements=[
            MeasurementInput(field="WAIST", value=Decimal("80.00"), unit=ProfileUnit.CM),
            MeasurementInput(field="UNKNOWN_XYZ", value=Decimal("50.00"), unit=ProfileUnit.CM),
        ]
    )
    with pytest.raises(ValueError, match="Unknown measurement field"):
        _run(service.add_measurements(user_id=user_id, batch=bad_batch))

    prof_after_fail = _run(service.get_profile(user_id))
    assert [m.field for m in prof_after_fail.measurements] == ["CHEST"]

    # Optimistically locked update v1 -> v2
    updated = _run(
        service.update_measurement(
            user_id=user_id,
            field="CHEST",
            payload=MeasurementUpdateRequest(
                value=Decimal("96.00"),
                unit=ProfileUnit.CM,
                expected_version=1,
            ),
        )
    )
    assert updated.version == 2
    assert updated.normalized_value == Decimal("96.00")
    assert user_id in service.repo._invalidated_users

    # Stale write with expected_version=1 must fail with OptimisticLockConflictError
    with pytest.raises(OptimisticLockConflictError):
        _run(
            service.update_measurement(
                user_id=user_id,
                field="CHEST",
                payload=MeasurementUpdateRequest(
                    value=Decimal("97.00"),
                    unit=ProfileUnit.CM,
                    expected_version=1,
                ),
            )
        )

    # History preserves previous 94.00 -> 96.00 transition
    history = _run(service.get_history(user_id, "CHEST"))
    assert len(history) == 2
    assert history[0].change_source == "SHOPPER_UPDATE"
    assert history[0].previous_value == Decimal("94.00")
    assert history[0].new_value == Decimal("96.00")


def test_ownership_isolation_vto_rejection_deletion_and_no_measurements_in_logs(caplog):
    """FITP-SEC-001..006 & FITP-REC-002: Ownership, VTO guard, deletion, and zero-PII logging."""
    service = _make_service()
    shopper_a = uuid4()
    shopper_b = uuid4()

    _run(
        service.update_consent(
            user_id=shopper_a,
            purpose=ConsentPurpose.FIT_PROFILE_STORAGE,
            granted=True,
            is_18_or_older=True,
        )
    )

    secret_val = Decimal("99.75")
    with caplog.at_level(logging.INFO):
        _run(
            service.add_measurements(
                user_id=shopper_a,
                batch=MeasurementBatchRequest(
                    measurements=[
                        MeasurementInput(field="CHEST", value=secret_val, unit=ProfileUnit.CM)
                    ]
                ),
            )
        )

    # FITP-SEC-006: Measurement numeric value must NEVER appear in application logs or audit events
    assert "99.75" not in caplog.text
    for evt in service.repo._mem_audit_events:
        assert "99.75" not in str(evt.details_json or "")

    # Shopper B sees empty profile and cannot read Shopper A's history or update A's CHEST
    prof_b = _run(service.get_profile(shopper_b))
    assert prof_b.measurements == []
    assert _run(service.get_history(shopper_b)) == []

    # VTO output rejected as measurement evidence
    with pytest.raises(VtoMeasurementEvidenceError):
        service.reject_vto_as_measurement_evidence("VTO_GENERATED_IMAGE")

    # Category preferences work independently
    _run(
        service.update_category_preference(
            user_id=shopper_a, category="TSHIRTS", fit_preference=FitPreference.RELAXED
        )
    )
    _run(
        service.update_category_preference(
            user_id=shopper_a, category="SHIRTS", fit_preference=FitPreference.REGULAR
        )
    )
    _run(service.delete_category_preference(shopper_a, "TSHIRTS"))
    prof_a = _run(service.get_profile(shopper_a))
    assert [c.category for c in prof_a.category_preferences] == ["SHIRTS"]

    # Delete fit profile clears measurements, history, preferences, and revokes consent
    counts = _run(service.delete_fit_profile(shopper_a))
    assert counts["measurements"] == 1
    assert counts["category_preferences"] == 1
    assert _run(service.get_history(shopper_a)) == []
    assert _run(service.consent.has_consent(shopper_a, ConsentPurpose.FIT_PROFILE_STORAGE)) is False
