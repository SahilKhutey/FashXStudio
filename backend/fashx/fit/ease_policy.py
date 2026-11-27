"""Ease and intended-fit policy governance (Phase 08.3 - Task 8.3.3).

Ease (G - B) MUST be treated as sourced product evidence, NEVER invented from a
shopper's subjective fit preference. By default no unverified ease rules are active;
callers may supply explicitly validated and versioned EaseRule instances backed by
merchant or specialist evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from fashx.fit.enums import FitPreference, MeasurementBasis


@dataclass(frozen=True)
class EaseRule:
    """Validated acceptable ease bounds for a garment category, measurement, and intended fit."""

    category: str
    measurement: str
    basis: MeasurementBasis
    intended_fit: FitPreference
    garment_construction: str
    minimum_cm: Decimal
    maximum_cm: Decimal
    policy_version: str
    evidence_reference: str

    def is_valid_range(self) -> bool:
        return self.minimum_cm <= self.maximum_cm


@dataclass(frozen=True)
class EaseEvaluationOutcome:
    """Result of checking calculated ease against an approved EaseRule."""

    evaluated: bool
    within_policy: bool
    calculated_ease_cm: Decimal | None
    rule: EaseRule | None
    reason: str


class EasePolicyRegistry:
    """Registry holding only explicitly approved, evidence-referenced ease rules."""

    def __init__(self, approved_rules: list[EaseRule] | None = None) -> None:
        self._rules: dict[tuple[str, str, MeasurementBasis, FitPreference], EaseRule] = {}
        for rule in approved_rules or []:
            if not rule.evidence_reference or not rule.evidence_reference.strip():
                raise ValueError("EaseRule requires a non-empty evidence_reference")
            if not rule.is_valid_range():
                raise ValueError(f"Invalid EaseRule bounds for {rule.category}/{rule.measurement}")
            key = (
                rule.category.strip().upper(),
                rule.measurement.strip().upper(),
                rule.basis,
                rule.intended_fit,
            )
            self._rules[key] = rule

    def get_rule(
        self,
        *,
        category: str,
        measurement: str,
        basis: MeasurementBasis,
        intended_fit: FitPreference,
    ) -> EaseRule | None:
        return self._rules.get(
            (category.strip().upper(), measurement.strip().upper(), basis, intended_fit)
        )


DEFAULT_EASE_REGISTRY = EasePolicyRegistry(approved_rules=[])


def evaluate_ease(
    *,
    body_cm: Decimal,
    garment_cm: Decimal,
    rule: EaseRule | None,
) -> EaseEvaluationOutcome:
    """Evaluate ease E = G - B strictly against an approved EaseRule.

    Never invents acceptable tolerances when rule is None.
    """
    ease = garment_cm - body_cm
    if rule is None:
        return EaseEvaluationOutcome(
            evaluated=False,
            within_policy=False,
            calculated_ease_cm=ease,
            rule=None,
            reason="FIT_POLICY_MISSING",
        )
    if not rule.is_valid_range():
        raise ValueError("EaseRule minimum_cm exceeds maximum_cm")

    matched = rule.minimum_cm <= ease <= rule.maximum_cm
    return EaseEvaluationOutcome(
        evaluated=True,
        within_policy=matched,
        calculated_ease_cm=ease,
        rule=rule,
        reason="EASE_WITHIN_POLICY" if matched else "OUTSIDE_EASE_POLICY",
    )
