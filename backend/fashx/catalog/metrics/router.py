from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from fashx.catalog.metrics.contracts import (
    CatalogMetricResult,
    EvaluationReport,
    TargetConfig,
    UsableProductCheckResult,
)
from fashx.catalog.metrics.evaluator import CatalogTargetEvaluator
from fashx.catalog.metrics.image_permission_metrics import (
    evaluate_image_permission_traceability,
)
from fashx.catalog.metrics.link_health import evaluate_link_health
from fashx.catalog.metrics.price_freshness import evaluate_price_freshness
from fashx.catalog.metrics.product_metrics import (
    evaluate_product_usability_metrics,
)
from fashx.catalog.metrics.report_service import CatalogReportService
from fashx.catalog.metrics.source_metrics import evaluate_source_metrics
from fashx.catalog.metrics.target_config import get_target_config
from fashx.core.database import get_db_session
from fashx.security.deps import Principal, get_principal, require_role

router = APIRouter(
    prefix="/admin/catalog",
    tags=["Catalog Target Metrics & Release Gates"],
    dependencies=[Depends(require_role("admin"))],
)


@router.get("/targets", response_model=TargetConfig)
async def get_configured_targets() -> TargetConfig:
    """Retrieve versioned pilot catalog targets and quality limits."""
    return get_target_config()


@router.post(
    "/evaluations",
    response_model=EvaluationReport,
    status_code=status.HTTP_201_CREATED,
)
async def start_evaluation_run(
    sample_size: int | None = Query(None, ge=1, le=1000),
    random_seed: int = Query(42),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
) -> EvaluationReport:
    """Trigger a comprehensive evaluation run against all catalog targets."""
    evaluator = CatalogTargetEvaluator(session)
    report = await evaluator.evaluate_all_targets(
        sample_size=sample_size,
        random_seed=random_seed,
    )

    # Persist evaluation report
    actor_id = None
    try:
        actor_id = UUID(principal.user_id)
    except Exception:
        pass

    report_svc = CatalogReportService(session)
    await report_svc.record_evaluation_run(report, created_by=actor_id)
    return report


@router.get("/evaluations/{id}", response_model=dict)
async def get_evaluation_status(
    id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Retrieve status and summary of a specific evaluation run."""
    report_svc = CatalogReportService(session)
    db_run = await report_svc.get_evaluation(id)
    if not db_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{id}' not found.",
        )
    return {
        "evaluation_id": str(db_run.id),
        "status": db_run.status,
        "all_passed": db_run.all_passed,
        "started_at": db_run.started_at,
        "completed_at": db_run.completed_at,
        "metrics_summary": db_run.metrics_summary,
    }


@router.get("/evaluations/{id}/report", response_model=dict)
async def get_evaluation_full_report(
    id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Retrieve the full detailed evaluation report."""
    report_svc = CatalogReportService(session)
    db_run = await report_svc.get_evaluation(id)
    if not db_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{id}' not found.",
        )
    return {
        "evaluation_id": str(db_run.id),
        "configuration_version": db_run.configuration_version,
        "status": db_run.status,
        "all_passed": db_run.all_passed,
        "started_at": db_run.started_at,
        "completed_at": db_run.completed_at,
        "metrics_summary": db_run.metrics_summary,
        "detailed_report": db_run.detailed_report,
    }


@router.get("/metrics", response_model=dict[str, CatalogMetricResult])
async def get_latest_metrics(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, CatalogMetricResult]:
    """Retrieve latest metric results across all 7 catalog targets."""
    evaluator = CatalogTargetEvaluator(session)
    report = await evaluator.evaluate_all_targets()
    return report.metric_results


@router.get("/source-health", response_model=dict)
async def view_source_health_and_authorization(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """View source health, live feeds, and authorization compliance details."""
    live_res, unauth_res, details = await evaluate_source_metrics(session)
    return {
        "live_sources_metric": live_res,
        "unauthorized_sources_metric": unauth_res,
        "source_reconciliation": details,
    }


@router.get("/quality", response_model=UsableProductCheckResult)
async def view_product_quality_results(
    session: AsyncSession = Depends(get_db_session),
) -> UsableProductCheckResult:
    """View usable product breakdown and rejection counts."""
    _, _, breakdown, _ = await evaluate_product_usability_metrics(session)
    return breakdown


@router.get("/price-freshness", response_model=dict)
async def view_price_freshness(
    sample_size: int = Query(100, ge=1, le=1000),
    random_seed: int = Query(42),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """View price freshness metrics and exception counts."""
    metric_res, details = await evaluate_price_freshness(
        session,
        sample_size=sample_size,
        random_seed=random_seed,
    )
    return {"metric": metric_res, "details": details}


@router.get("/link-health", response_model=dict)
async def view_link_health(
    sample_size: int = Query(100, ge=1, le=1000),
    random_seed: int = Query(42),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """View product link health, classifications, and broken link rate."""
    metric_res, details = await evaluate_link_health(
        session,
        sample_size=sample_size,
        random_seed=random_seed,
    )
    return {"metric": metric_res, "details": details}


@router.get("/image-compliance", response_model=dict)
async def view_image_compliance(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """View image permission traceability and operational rights breakdown."""
    metric_res, details = await evaluate_image_permission_traceability(session)
    return {"metric": metric_res, "details": details}
