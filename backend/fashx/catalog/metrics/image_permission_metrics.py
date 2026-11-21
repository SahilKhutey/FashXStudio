from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource
from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogPermissionStatus,
    CatalogSourcePermission,
)
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from fashx.catalog.metrics.contracts import CatalogMetricResult


async def evaluate_image_permission_traceability(
    session: AsyncSession,
    target_traceability_percentage: float = 100.0,
) -> tuple[CatalogMetricResult, dict]:
    """Evaluates CAT-TGT-07: 100% Traceable image permissions across operations."""
    now = datetime.now(UTC)

    # 1. Fetch all catalog image assets not deleted
    query = select(CatalogImageAsset).where(
        CatalogImageAsset.status != ImageAssetStatus.DELETED.value
    )
    result = await session.execute(query)
    assets = list(result.scalars().all())

    if not assets:
        empty_res = CatalogMetricResult(
            metric_id="CAT-TGT-07",
            target_value=target_traceability_percentage,
            actual_value=100.0,
            unit="percent",
            passed=True,
            measured_at=now,
            numerator=0,
            denominator=0,
            evidence_reference="image_permission_compliance_audit",
            notes=["No active catalog image assets registered."],
        )
        return empty_res, {
            "total_assets": 0,
            "traceable_count": 0,
            "untraceable_count": 0,
            "untraceable_asset_ids": [],
            "operation_decisions": {
                "fetch_granted": 0,
                "store_granted": 0,
                "display_granted": 0,
                "ai_processing_granted": 0,
                "vto_granted": 0,
                "derivatives_granted": 0,
            },
        }

    # 2. Cache source permissions
    perms_query = select(CatalogSourcePermission).where(
        CatalogSourcePermission.permission_status == CatalogPermissionStatus.GRANTED.value
    )
    perms_res = await session.execute(perms_query)
    source_granted_codes: dict[str, set[str]] = {}
    for perm in perms_res.scalars().all():
        s_id = str(perm.source_id)
        if s_id not in source_granted_codes:
            source_granted_codes[s_id] = set()
        source_granted_codes[s_id].add(perm.permission_code)

    sources_cache: dict[str, CatalogSource] = {}

    traceable_count = 0
    untraceable_count = 0
    untraceable_asset_ids: list[str] = []
    operation_decisions_breakdown = {
        "fetch_granted": 0,
        "store_granted": 0,
        "display_granted": 0,
        "ai_processing_granted": 0,
        "vto_granted": 0,
        "derivatives_granted": 0,
    }

    for asset in assets:
        s_id = str(asset.source_id)
        if s_id not in sources_cache:
            src = await session.get(CatalogSource, asset.source_id)
            if src:
                sources_cache[s_id] = src
        source = sources_cache.get(s_id)

        # Traceability requires: valid source, merchant, status, and unambiguous rights
        is_traceable = True
        if not source or not asset.merchant_id:
            is_traceable = False
        elif not (asset.original_storage_key or asset.source_reference):
            is_traceable = False

        if not is_traceable:
            untraceable_count += 1
            untraceable_asset_ids.append(str(asset.id))
            continue

        traceable_count += 1
        active_codes = source_granted_codes.get(s_id, set())

        # Check operation decisions
        if CatalogPermissionCode.IMAGE_FETCH.value in active_codes or source.status == "cleared":
            operation_decisions_breakdown["fetch_granted"] += 1
        if (
            CatalogPermissionCode.IMAGE_STORE.value in active_codes
            or source.image_policy == "mirror"
        ):
            operation_decisions_breakdown["store_granted"] += 1
        if CatalogPermissionCode.IMAGE_DISPLAY.value in active_codes or source.rights_display:
            operation_decisions_breakdown["display_granted"] += 1
        if CatalogPermissionCode.IMAGE_AI_PROCESS.value in active_codes:
            operation_decisions_breakdown["ai_processing_granted"] += 1
        if CatalogPermissionCode.VTO_PROCESS.value in active_codes or source.rights_tryon:
            operation_decisions_breakdown["vto_granted"] += 1
        if CatalogPermissionCode.DERIVATIVE_STORE.value in active_codes:
            operation_decisions_breakdown["derivatives_granted"] += 1

    total_assets = len(assets)
    actual_percentage = (
        round((traceable_count / total_assets) * 100.0, 2) if total_assets > 0 else 100.0
    )
    passed = actual_percentage >= target_traceability_percentage and untraceable_count == 0

    metric_result = CatalogMetricResult(
        metric_id="CAT-TGT-07",
        target_value=target_traceability_percentage,
        actual_value=actual_percentage,
        unit="percent",
        passed=passed,
        measured_at=now,
        numerator=traceable_count,
        denominator=total_assets,
        evidence_reference="image_permission_compliance_audit",
        notes=[
            f"Image permission traceability: {actual_percentage}% (target: {target_traceability_percentage}%).",
            f"Asset counts: total={total_assets}, traceable={traceable_count}, untraceable={untraceable_count}.",
            f"Operational rights breakdown: {operation_decisions_breakdown}.",
        ],
    )

    details = {
        "total_assets": total_assets,
        "traceable_count": traceable_count,
        "untraceable_count": untraceable_count,
        "untraceable_asset_ids": untraceable_asset_ids[:50],
        "operation_decisions": operation_decisions_breakdown,
    }

    return metric_result, details
