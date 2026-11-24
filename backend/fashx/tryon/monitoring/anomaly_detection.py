"""Anomaly detection and spend alerting for Virtual Try-On inference.

Detects:
1. Multi-tier budget thresholds:
   - Warning at 70% of ceiling
   - Critical at 90% of ceiling
   - Hard Stop at 100% of ceiling
2. Spend velocity spikes (e.g. burn rate accelerating 3x over baseline)
3. Abnormal failure surges on paid inference operations
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

logger = logging.getLogger(__name__)


class BudgetAlertLevel(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EXCEEDED = "EXCEEDED"


@dataclass
class BudgetEvaluation:
    """Outcome of budget threshold analysis."""

    alert_level: BudgetAlertLevel
    utilization_pct: Decimal
    current_spend_usd: Decimal
    reserved_spend_usd: Decimal
    hard_limit_amount: Decimal
    alert_message: str | None = None


class TryOnAnomalyDetector:
    """Evaluates spend velocity, failure spikes, and budget threshold violations."""

    @staticmethod
    def evaluate_budget(
        current_spend_usd: Decimal,
        reserved_spend_usd: Decimal,
        hard_limit_amount: Decimal,
        warn_threshold_pct: Decimal = Decimal("70.00"),
        crit_threshold_pct: Decimal = Decimal("90.00"),
    ) -> BudgetEvaluation:
        """Evaluate spending utilization against configured threshold tiers."""
        if hard_limit_amount <= Decimal("0.0000"):
            return BudgetEvaluation(
                alert_level=BudgetAlertLevel.EXCEEDED,
                utilization_pct=Decimal("100.00"),
                current_spend_usd=current_spend_usd,
                reserved_spend_usd=reserved_spend_usd,
                hard_limit_amount=hard_limit_amount,
                alert_message="Hard limit amount is zero or negative.",
            )

        total_committed_or_reserved = current_spend_usd + reserved_spend_usd
        utilization_pct = (
            (total_committed_or_reserved / hard_limit_amount) * Decimal("100.0")
        ).quantize(Decimal("0.01"))

        if utilization_pct >= Decimal("100.00"):
            level = BudgetAlertLevel.EXCEEDED
            msg = f"Budget EXCEEDED: {utilization_pct}% utilization (${total_committed_or_reserved} / ${hard_limit_amount})"
            logger.critical(msg)
        elif utilization_pct >= crit_threshold_pct:
            level = BudgetAlertLevel.CRITICAL
            msg = f"Budget CRITICAL: {utilization_pct}% utilization reached (threshold: {crit_threshold_pct}%)"
            logger.error(msg)
        elif utilization_pct >= warn_threshold_pct:
            level = BudgetAlertLevel.WARNING
            msg = f"Budget WARNING: {utilization_pct}% utilization reached (threshold: {warn_threshold_pct}%)"
            logger.warning(msg)
        else:
            level = BudgetAlertLevel.NORMAL
            msg = None

        return BudgetEvaluation(
            alert_level=level,
            utilization_pct=utilization_pct,
            current_spend_usd=current_spend_usd,
            reserved_spend_usd=reserved_spend_usd,
            hard_limit_amount=hard_limit_amount,
            alert_message=msg,
        )

    @staticmethod
    def detect_spend_velocity_surge(
        recent_window_spend: Decimal,
        baseline_window_spend: Decimal,
        acceleration_factor_threshold: Decimal = Decimal("3.0"),
    ) -> bool:
        """Detect if spend acceleration in the recent window exceeds normal baseline."""
        if baseline_window_spend <= Decimal("0.0100"):
            # If baseline is near zero, only flag if absolute recent spend is material
            return recent_window_spend >= Decimal("25.0000")

        ratio = recent_window_spend / baseline_window_spend
        if ratio >= acceleration_factor_threshold:
            logger.warning(
                "SPEND SURGE DETECTED: Recent window ($%s) is %sx baseline ($%s)",
                recent_window_spend,
                ratio.quantize(Decimal("0.1")),
                baseline_window_spend,
            )
            return True
        return False
