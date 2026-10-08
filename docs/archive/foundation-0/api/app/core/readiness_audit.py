from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    name: str
    passed: bool
    score: float | None = None
    target_sla: str = ""
    details: dict[str, Any] | None = None


class ProductionReadinessAuditor:
    """Evaluates the Six Explicit Production Release Gates (Roadmap Phase 6: G1–G6)."""

    @classmethod
    def audit_g2_ml_quality(
        cls,
        attribute_completeness: float,
        silhouette_accuracy: float,
        color_accuracy: float,
    ) -> GateResult:
        r"""G2: ML Quality Gate (Enrichment $\ge 95\%$, Silhouette $\ge 92\%$, Color $\ge 95\%$)."""
        passed = (
            attribute_completeness >= 0.95
            and silhouette_accuracy >= 0.92
            and color_accuracy >= 0.95
        )
        return GateResult(
            gate_id="G2",
            name="ML Quality Gate",
            passed=passed,
            score=round(
                (attribute_completeness + silhouette_accuracy + color_accuracy) / 3.0,
                3,
            ),
            target_sla="Attribute Completeness >= 95%, Silhouette >= 92%, Color >= 95%",
            details={
                "attribute_completeness": attribute_completeness,
                "silhouette_accuracy": silhouette_accuracy,
                "color_accuracy": color_accuracy,
            },
        )

    @classmethod
    def audit_g3_performance(
        cls,
        api_p95_ms: float,
        feed_latency_ms: float,
        tryon_latency_sec: float,
    ) -> GateResult:
        """G3: Performance Gate (API p95 $<150$ms, Feed $<300$ms, Try-On $<6$s)."""
        passed = api_p95_ms <= 150.0 and feed_latency_ms <= 300.0 and tryon_latency_sec <= 6.0
        return GateResult(
            gate_id="G3",
            name="Performance Gate",
            passed=passed,
            target_sla="API p95 < 150ms, Feed < 300ms, Try-On GPU < 6.0s",
            details={
                "api_p95_ms": api_p95_ms,
                "feed_latency_ms": feed_latency_ms,
                "tryon_latency_sec": tryon_latency_sec,
            },
        )

    @classmethod
    def audit_g4_privacy(
        cls,
        photos_purged: int,
        storage_objects_purged: int,
        residual_leaked_count: int = 0,
    ) -> GateResult:
        """G4: Privacy Gate (Consent revocation instantly cascades hard deletions)."""
        passed = residual_leaked_count == 0 and photos_purged == storage_objects_purged
        return GateResult(
            gate_id="G4",
            name="Privacy & Data Erasure Gate",
            passed=passed,
            target_sla="Zero residual photos or database records upon consent revocation",
            details={
                "photos_purged": photos_purged,
                "storage_objects_purged": storage_objects_purged,
                "residual_leaked_count": residual_leaked_count,
            },
        )

    @classmethod
    def audit_g5_commercial_clearance(
        cls,
        environment: str,
        is_model_commercial_cleared: bool,
        has_affiliate_attribution: bool,
    ) -> GateResult:
        """G5: Commercial Gate (Model licenses verified for commercial production use)."""
        if environment == "production":
            passed = is_model_commercial_cleared and has_affiliate_attribution
        else:
            # Test / Evaluation environments can run evaluation models
            passed = has_affiliate_attribution

        return GateResult(
            gate_id="G5",
            name="Commercial Authorization Gate",
            passed=passed,
            target_sla="Zero un-cleared research weights in production, verified affiliate tracking",
            details={
                "environment": environment,
                "is_model_commercial_cleared": is_model_commercial_cleared,
                "has_affiliate_attribution": has_affiliate_attribution,
            },
        )

    @classmethod
    def audit_g6_user_acceptance(
        cls,
        tryon_realism_satisfaction_pct: float,
        feed_relevance_satisfaction_pct: float,
    ) -> GateResult:
        """G6: User Acceptance Gate (>75% tryon realism satisfaction, >80% feed relevance)."""
        passed = tryon_realism_satisfaction_pct >= 75.0 and feed_relevance_satisfaction_pct >= 80.0
        return GateResult(
            gate_id="G6",
            name="User Acceptance Gate",
            passed=passed,
            target_sla="Try-on Realism >= 75%, Feed Relevance >= 80%",
            details={
                "tryon_realism_satisfaction_pct": tryon_realism_satisfaction_pct,
                "feed_relevance_satisfaction_pct": feed_relevance_satisfaction_pct,
            },
        )
