"""Tests for Shopper Fit Profile FastAPI Routes & Ownership (Phase 08.2)."""

from __future__ import annotations

import inspect
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from fashx.main import app
from fashx.profile.consent import FitConsentService
from fashx.profile.fit_router import (
    add_fit_measurements,
    clear_category_fit_preference,
    delete_fit_measurement,
    delete_fit_profile,
    get_category_fit_policy,
    get_fit_profile,
    get_measurement_definitions,
    list_measurement_history,
    update_category_fit_preference,
    update_default_fit_preference,
    update_fit_consent,
    update_fit_measurement,
)
from fashx.profile.fit_schemas import (
    CategoryPreferenceUpdateRequest,
    ConsentPurpose,
    FitConsentUpdateRequest,
    FitPreference,
    MeasurementBatchRequest,
    MeasurementInput,
    MeasurementUpdateRequest,
    PreferenceUpdateRequest,
)
from fashx.profile.repositories.fit_profile_repository import FitProfileRepository
from fashx.profile.services.fit_profile_service import FitProfileService
from fashx.profile.units import ProfileUnit
from fashx.security.deps import Principal, get_principal


def _run(coro):
    """Run an async coroutine synchronously without creating a Windows Proactor loop."""
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


class _FakeProfileUOW:
    def __init__(self):
        self.session = None
        self.committed = False

    async def commit(self):
        self.committed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def test_fit_profile_routes_mounted_with_get_principal():
    """Verify /api/v1/profile/fit endpoints exist in OpenAPI and require authentication."""
    spec_paths = app.openapi()["paths"]
    expected = [
        ("/api/v1/profile/fit", ("get", "delete")),
        ("/api/v1/profile/fit/measurements", ("post",)),
        ("/api/v1/profile/fit/measurements/{field}", ("patch", "delete")),
        ("/api/v1/profile/fit/measurements/history", ("get",)),
        ("/api/v1/profile/fit/preferences", ("put",)),
        ("/api/v1/profile/fit/preferences/{category}", ("put", "delete")),
        ("/api/v1/profile/fit/policies/{category}", ("get",)),
        ("/api/v1/profile/fit/definitions", ("get",)),
        ("/api/v1/profile/fit/consents", ("get",)),
        ("/api/v1/profile/fit/consents/{purpose}", ("put",)),
    ]
    for path, methods in expected:
        assert path in spec_paths, f"Missing path {path}"
        for m in methods:
            assert m in spec_paths[path], f"Missing method {m} on {path}"

    mounted = [
        r
        for r in app.routes
        if hasattr(r, "original_router")
        and getattr(getattr(r, "original_router", None), "prefix", None) == "/profile/fit"
    ]
    assert len(mounted) == 1
    deps = {
        getattr(d, "dependency", None)
        for d in getattr(mounted[0].include_context, "dependencies", ())
    }
    assert get_principal in deps


def test_fit_profile_api_end_to_end_flow():
    """Exercise full FastAPI fit-profile endpoints using authenticated principal & fake UOW."""
    shopper_id = uuid4()
    other_shopper_id = uuid4()
    principal_a = Principal(user_id=str(shopper_id), subject="shopper-a", roles=frozenset({"user"}))
    principal_b = Principal(
        user_id=str(other_shopper_id), subject="shopper-b", roles=frozenset({"user"})
    )
    uow = _FakeProfileUOW()
    service = FitProfileService(
        repository=FitProfileRepository(),
        consent_service=FitConsentService(),
    )

    with patch("fashx.profile.fit_router._build_service", lambda _uow: service):
        # 1. Incomplete profile initially; browse/readiness still works
        prof0 = _run(get_fit_profile(principal=principal_a, uow=uow))
        assert prof0.status == "PROFILE_INCOMPLETE"
        assert prof0.default_fit_preference == FitPreference.NO_PREFERENCE
        assert prof0.category_readiness["TSHIRTS"].missing_fields == ["CHEST"]

        # 2. Saving measurement without storage consent -> HTTP 403
        batch = MeasurementBatchRequest(
            measurements=[MeasurementInput(field="CHEST", value=Decimal("98"), unit=ProfileUnit.CM)]
        )
        with pytest.raises(HTTPException) as exc_consent:
            _run(add_fit_measurements(batch, principal=principal_a, uow=uow))
        assert exc_consent.value.status_code == 403

        # 3. Grant FIT_PROFILE_STORAGE consent -> save succeeds -> T-shirts ready!
        _run(
            update_fit_consent(
                ConsentPurpose.FIT_PROFILE_STORAGE,
                FitConsentUpdateRequest(granted=True, is_18_or_older=True),
                principal=principal_a,
                uow=uow,
            )
        )
        prof1 = _run(add_fit_measurements(batch, principal=principal_a, uow=uow))
        assert prof1.status == "PROFILE_READY"
        assert prof1.category_readiness["TSHIRTS"].status == "READY"
        assert uow.committed is True

        # 4. Update with wrong version -> HTTP 409 conflict
        with pytest.raises(HTTPException) as exc_conflict:
            _run(
                update_fit_measurement(
                    "CHEST",
                    MeasurementUpdateRequest(
                        value=Decimal("99"), unit=ProfileUnit.CM, expected_version=99
                    ),
                    principal=principal_a,
                    uow=uow,
                )
            )
        assert exc_conflict.value.status_code == 409

        # 5. Update with right version -> version 2 & history recorded
        updated = _run(
            update_fit_measurement(
                "CHEST",
                MeasurementUpdateRequest(
                    value=Decimal("39"), unit=ProfileUnit.IN, expected_version=1
                ),
                principal=principal_a,
                uow=uow,
            )
        )
        assert updated.version == 2
        assert updated.normalized_value == Decimal("99.06")

        hist = _run(list_measurement_history(field="CHEST", principal=principal_a, uow=uow))
        assert len(hist) == 2

        # 6. Different shopper cannot read or delete shopper_a's data
        prof_b = _run(get_fit_profile(principal=principal_b, uow=uow))
        assert prof_b.measurements == []
        with pytest.raises(HTTPException) as exc_del_b:
            _run(delete_fit_measurement("CHEST", principal=principal_b, uow=uow))
        assert exc_del_b.value.status_code == 404

        # 7. Default and category preferences + definitions + policy
        _run(
            update_default_fit_preference(
                PreferenceUpdateRequest(
                    default_fit_preference=FitPreference.REGULAR,
                    preferred_unit=ProfileUnit.IN,
                ),
                principal=principal_a,
                uow=uow,
            )
        )
        cat_pref = _run(
            update_category_fit_preference(
                "TSHIRTS",
                CategoryPreferenceUpdateRequest(fit_preference=FitPreference.RELAXED),
                principal=principal_a,
                uow=uow,
            )
        )
        assert cat_pref.fit_preference == FitPreference.RELAXED
        _run(clear_category_fit_preference("TSHIRTS", principal=principal_a, uow=uow))

        defs = _run(get_measurement_definitions(principal=principal_a))
        assert any(d.code == "CHEST" for d in defs)

        pol = _run(get_category_fit_policy("TROUSERS", principal=principal_a, uow=uow))
        assert pol.missing_fields == ["WAIST", "HIP"]

        # 8. Delete entire fit profile -> 204 & history wiped
        _run(delete_fit_profile(principal=principal_a, uow=uow))
        assert _run(list_measurement_history(field=None, principal=principal_a, uow=uow)) == []
