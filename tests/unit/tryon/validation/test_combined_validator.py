"""Unit tests for CombinedVTOInputValidator (Phase 07.3)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fashx.tryon.validation.combined_validator import CombinedVTOInputValidator
from fashx.tryon.validation.contracts import (
    ImageRole,
    ImageValidationResult,
    Severity,
    ValidationIssue,
    ValidationRequest,
    ValidationStatus,
)


class StubValidator:
    def __init__(self, result: ImageValidationResult) -> None:
        self.result = result

    async def validate(self, **kwargs: object) -> ImageValidationResult:
        return self.result


def make_result(role: ImageRole, status: ValidationStatus) -> ImageValidationResult:
    issues = []
    if status == ValidationStatus.REJECTED:
        issues.append(
            ValidationIssue(
                code="REJECTED_CODE",
                severity=Severity.ERROR,
                message="Error message",
                user_message="User error message",
            )
        )
    elif status == ValidationStatus.PASSED_WITH_WARNINGS:
        issues.append(
            ValidationIssue(
                code="WARN_CODE",
                severity=Severity.WARNING,
                message="Warning message",
                user_message="User warning message",
            )
        )
    return ImageValidationResult(
        role=role,
        status=status,
        asset_id=str(uuid4()),
        asset_version="v1",
        policy_version="v1",
        issues=issues,
    )


@pytest.mark.asyncio
async def test_combined_both_pass() -> None:
    shopper = make_result(ImageRole.SHOPPER, ValidationStatus.PASSED)
    garment = make_result(ImageRole.GARMENT, ValidationStatus.PASSED)
    validator = CombinedVTOInputValidator(
        shopper_validator=StubValidator(shopper),  # type: ignore[arg-type]
        garment_validator=StubValidator(garment),  # type: ignore[arg-type]
    )
    req = ValidationRequest(
        user_id=uuid4(),
        shopper_asset_id=uuid4(),
        product_id=uuid4(),
    )
    res = await validator.validate(req)
    assert res.status == ValidationStatus.PASSED
    assert res.can_submit is True


@pytest.mark.asyncio
async def test_combined_shopper_rejected() -> None:
    shopper = make_result(ImageRole.SHOPPER, ValidationStatus.REJECTED)
    garment = make_result(ImageRole.GARMENT, ValidationStatus.PASSED)
    validator = CombinedVTOInputValidator(
        shopper_validator=StubValidator(shopper),  # type: ignore[arg-type]
        garment_validator=StubValidator(garment),  # type: ignore[arg-type]
    )
    req = ValidationRequest(
        user_id=uuid4(),
        shopper_asset_id=uuid4(),
        product_id=uuid4(),
    )
    res = await validator.validate(req)
    assert res.status == ValidationStatus.REJECTED
    assert res.can_submit is False


@pytest.mark.asyncio
async def test_combined_garment_rejected() -> None:
    shopper = make_result(ImageRole.SHOPPER, ValidationStatus.PASSED)
    garment = make_result(ImageRole.GARMENT, ValidationStatus.REJECTED)
    validator = CombinedVTOInputValidator(
        shopper_validator=StubValidator(shopper),  # type: ignore[arg-type]
        garment_validator=StubValidator(garment),  # type: ignore[arg-type]
    )
    req = ValidationRequest(
        user_id=uuid4(),
        shopper_asset_id=uuid4(),
        product_id=uuid4(),
    )
    res = await validator.validate(req)
    assert res.status == ValidationStatus.REJECTED
    assert res.can_submit is False


@pytest.mark.asyncio
async def test_combined_warnings_allowed() -> None:
    shopper = make_result(ImageRole.SHOPPER, ValidationStatus.PASSED_WITH_WARNINGS)
    garment = make_result(ImageRole.GARMENT, ValidationStatus.PASSED)
    validator = CombinedVTOInputValidator(
        shopper_validator=StubValidator(shopper),  # type: ignore[arg-type]
        garment_validator=StubValidator(garment),  # type: ignore[arg-type]
    )
    req = ValidationRequest(
        user_id=uuid4(),
        shopper_asset_id=uuid4(),
        product_id=uuid4(),
    )
    res = await validator.validate(req)
    assert res.status == ValidationStatus.PASSED_WITH_WARNINGS
    assert res.can_submit is True
