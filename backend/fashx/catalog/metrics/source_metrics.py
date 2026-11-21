from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource, IngestRun, Merchant
from database.models.catalog_auth import (
    CatalogAuthorizationEvidence,
    CatalogSourceStatus,
)
from fashx.catalog.metrics.contracts import CatalogMetricResult

DISQUALIFYING_ADAPTER_SUBSTRINGS = ("mock", "fixture", "test_stub", "seed_file")
DISQUALIFYING_KINDS = ("manual", "file_drop_fixture")


async def evaluate_source_metrics(
    session: AsyncSession,
    minimum_live_sources: int = 1,
    maximum_unauthorized_sources: int = 0,
) -> tuple[CatalogMetricResult, CatalogMetricResult, dict]:
    """Evaluates CAT-TGT-01 (Live Authorized Feeds) and CAT-TGT-06 (Zero Unauthorized Sources)."""
    now = datetime.now(UTC)
    sources_res = await session.execute(select(CatalogSource))
    all_sources = list(sources_res.scalars().all())

    # Pre-fetch verified evidence source_ids
    evidence_res = await session.execute(
        select(CatalogAuthorizationEvidence.source_id).where(
            CatalogAuthorizationEvidence.verification_status.in_(["VERIFIED", "APPROVED"])
        )
    )
    sources_with_verified_evidence = set(evidence_res.scalars().all())

    qualified_live_source_ids: list[str] = []
    unauthorized_source_ids: list[str] = []
    source_reconciliation_details: list[dict] = []

    for src in all_sources:
        is_mock_or_fixture = (
            any(sub in (src.adapter_name or "").lower() for sub in DISQUALIFYING_ADAPTER_SUBSTRINGS)
            or src.kind.lower() in DISQUALIFYING_KINDS
        )

        has_auth_evidence = bool(src.authorization_reference or src.terms_url) or (
            src.id in sources_with_verified_evidence
        )

        is_authorized = (
            src.source_status
            in (
                CatalogSourceStatus.APPROVED.value,
                CatalogSourceStatus.ACTIVE.value,
                "AUTHORIZED",
            )
            and src.source_status
            not in (
                CatalogSourceStatus.SUSPENDED.value,
                CatalogSourceStatus.REVOKED.value,
                CatalogSourceStatus.EXPIRED.value,
            )
            and (src.expires_at is None or src.expires_at > now)
            and has_auth_evidence
        )

        # Compliance Check (CAT-TGT-06): If source is operational/enabled or cleared but lacks valid authorization
        if (src.is_enabled or src.status == "cleared") and not is_authorized:
            unauthorized_source_ids.append(str(src.id))

        # Live Feed Check (CAT-TGT-01):
        # Must be authorized, enabled, merchant verified, not a mock, and have completed at least one successful ingest run
        is_live_qualified = False
        rejection_reasons = []

        if not is_authorized:
            rejection_reasons.append(
                "Source lacks approved authorization reference or is expired/suspended"
            )
        if not src.is_enabled:
            rejection_reasons.append("Source operational status is not enabled")
        if is_mock_or_fixture:
            rejection_reasons.append(
                "Mock, fixture, or manual test feeds are ineligible for live feed metric"
            )

        # Check merchant verification
        merchant = await session.get(Merchant, src.merchant_id) if src.merchant_id else None
        if not merchant or merchant.verification_status not in ("VERIFIED", "ACTIVE"):
            rejection_reasons.append("Merchant identity is unverified")

        # Check successful synchronization against actual source
        successful_run = await session.scalar(
            select(IngestRun)
            .where(
                IngestRun.source_id == src.id,
                IngestRun.status.in_(["ok", "completed"]),
            )
            .limit(1)
        )
        if not successful_run:
            rejection_reasons.append("No recorded successful synchronization run")

        if not rejection_reasons:
            is_live_qualified = True
            qualified_live_source_ids.append(str(src.id))

        source_reconciliation_details.append(
            {
                "source_id": str(src.id),
                "slug": src.slug,
                "merchant_id": str(src.merchant_id) if src.merchant_id else None,
                "is_authorized": is_authorized,
                "is_enabled": src.is_enabled,
                "is_live_qualified": is_live_qualified,
                "rejection_reasons": rejection_reasons,
            }
        )

    # Metric 1: CAT-TGT-01 (At least 1 live authorized merchant feed)
    live_count = len(qualified_live_source_ids)
    live_passed = live_count >= minimum_live_sources
    live_result = CatalogMetricResult(
        metric_id="CAT-TGT-01",
        target_value=float(minimum_live_sources),
        actual_value=float(live_count),
        unit="sources",
        passed=live_passed,
        measured_at=now,
        numerator=live_count,
        denominator=minimum_live_sources,
        source_ids=qualified_live_source_ids,
        evidence_reference="source_verification_report",
        notes=[
            f"Qualified live feeds: {live_count}/{minimum_live_sources}.",
            "Excludes mock adapters, fixtures, and unverified feeds per Section 3.1.",
        ],
    )

    # Metric 2: CAT-TGT-06 (Zero unauthorized sources)
    unauthorized_count = len(unauthorized_source_ids)
    unauthorized_passed = unauthorized_count <= maximum_unauthorized_sources
    unauthorized_result = CatalogMetricResult(
        metric_id="CAT-TGT-06",
        target_value=float(maximum_unauthorized_sources),
        actual_value=float(unauthorized_count),
        unit="sources",
        passed=unauthorized_passed,
        measured_at=now,
        numerator=unauthorized_count,
        denominator=len(all_sources),
        source_ids=unauthorized_source_ids,
        evidence_reference="source_authorization_compliance_audit",
        notes=[
            f"Active unauthorized sources detected: {unauthorized_count}.",
            "Absolute compliance gate: zero tolerance permitted.",
        ],
    )

    return live_result, unauthorized_result, {"sources": source_reconciliation_details}
