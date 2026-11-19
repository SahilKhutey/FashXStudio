from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from fashx.catalog.metrics.contracts import (
    CatalogMetricResult,
    EvaluationReport,
    LinkCheckResult,
    TargetConfig,
)
from fashx.catalog.metrics.image_permission_metrics import (
    evaluate_image_permission_traceability,
)
from fashx.catalog.metrics.link_health import evaluate_link_health
from fashx.catalog.metrics.price_freshness import evaluate_price_freshness
from fashx.catalog.metrics.product_metrics import (
    evaluate_product_usability_metrics,
)
from fashx.catalog.metrics.source_metrics import evaluate_source_metrics
from fashx.catalog.metrics.target_config import get_target_config


class CatalogTargetEvaluator:
    def __init__(
        self,
        session: AsyncSession,
        config: TargetConfig | None = None,
    ) -> None:
        self.session = session
        self.config = config or get_target_config()

    async def evaluate_all_targets(
        self,
        sample_size: int | None = None,
        random_seed: int = 42,
        link_check_fn: Callable[[str], LinkCheckResult] | None = None,
    ) -> EvaluationReport:
        evaluation_id = uuid.uuid4()
        started_at = datetime.now(UTC)

        # 1. Source Metrics (CAT-TGT-01, CAT-TGT-06)
        live_res, unauth_res, source_details = await evaluate_source_metrics(
            self.session,
            minimum_live_sources=self.config.pilot.minimum_live_authorized_sources,
            maximum_unauthorized_sources=self.config.quality.maximum_unauthorized_sources,
        )

        # 2. Product Usability Metrics (CAT-TGT-02, CAT-TGT-03)
        (
            usable_res,
            expansion_res,
            breakdown,
            prod_details,
        ) = await evaluate_product_usability_metrics(
            self.session,
            minimum_usable_offers=self.config.pilot.minimum_usable_offers,
            expansion_minimum_offers=self.config.pilot.expansion_minimum_offers,
            expansion_maximum_offers=self.config.pilot.expansion_maximum_offers,
        )

        # 3. Price Freshness Metrics (CAT-TGT-04)
        freshness_res, freshness_details = await evaluate_price_freshness(
            self.session,
            sample_size=sample_size or self.config.sampling.default_sample_size,
            random_seed=random_seed,
            minimum_fresh_percentage=self.config.quality.minimum_fresh_price_percentage,
        )

        # 4. Product Link Health Metrics (CAT-TGT-05)
        link_res, link_details = await evaluate_link_health(
            self.session,
            sample_size=sample_size or self.config.sampling.default_sample_size,
            random_seed=random_seed,
            maximum_broken_percentage=self.config.quality.maximum_broken_link_percentage_exclusive,
            check_fn=link_check_fn,
        )

        # 5. Image Permission Traceability Metrics (CAT-TGT-07)
        image_res, image_details = await evaluate_image_permission_traceability(
            self.session,
            target_traceability_percentage=self.config.quality.minimum_image_permission_traceability_percentage,
        )

        # Compile metric results dictionary
        metric_results: dict[str, CatalogMetricResult] = {
            "CAT-TGT-01": live_res,
            "CAT-TGT-02": usable_res,
            "CAT-TGT-03": expansion_res,
            "CAT-TGT-04": freshness_res,
            "CAT-TGT-05": link_res,
            "CAT-TGT-06": unauth_res,
            "CAT-TGT-07": image_res,
        }

        # Release Gating Logic
        blockers: list[str] = []

        # Gate 1: Source Compliance (Absolute gate: 0 unauthorized sources)
        if not unauth_res.passed:
            blockers.append(
                f"Source Compliance Blocker: {int(unauth_res.actual_value)} unauthorized active sources detected."
            )

        # Gate 2: Image Compliance (Absolute gate: 100% traceability)
        if not image_res.passed:
            blockers.append(
                f"Image Compliance Blocker: Image permission traceability is {image_res.actual_value}% (< 100%)."
            )

        # Gate 3: Live Feed Authorization
        if not live_res.passed:
            blockers.append(
                f"Live Feed Blocker: {int(live_res.actual_value)} qualified live feeds (target: >= {int(live_res.target_value)})."
            )

        # Gate 4: Usable Product Count
        if not usable_res.passed:
            blockers.append(
                f"Usable Catalog Blocker: {int(usable_res.actual_value)} usable offers (target: >= {int(usable_res.target_value)})."
            )

        # Gate 5: Price Freshness
        if not freshness_res.passed:
            blockers.append(
                f"Price Freshness Blocker: {freshness_res.actual_value}% fresh prices (target: >= {freshness_res.target_value}%)."
            )

        # Gate 6: Link Health
        if not link_res.passed:
            blockers.append(
                f"Link Health Blocker: {link_res.actual_value}% broken links (target: < {link_res.target_value}%)."
            )

        all_passed = len(blockers) == 0
        release_decision = "ACCEPT" if all_passed else "HOLD"
        completed_at = datetime.now(UTC)

        evidence_references = [
            "docs/catalog/PHASE_05_7_INITIAL_CATALOG_TARGETS.md",
            "docs/catalog/PHASE_05_7_METRIC_DEFINITIONS.md",
            "docs/catalog/PHASE_05_7_ACCEPTANCE_REPORT.md",
        ]

        return EvaluationReport(
            evaluation_id=evaluation_id,
            configuration_version=self.config.version,
            status="COMPLETED",
            started_at=started_at,
            completed_at=completed_at,
            all_passed=all_passed,
            metric_results=metric_results,
            usable_product_breakdown=breakdown,
            release_decision=release_decision,
            blockers=blockers,
            evidence_references=evidence_references,
        )
