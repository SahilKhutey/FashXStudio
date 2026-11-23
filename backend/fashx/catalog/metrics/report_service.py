from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_evaluation import CatalogEvaluationRun
from fashx.catalog.metrics.contracts import EvaluationReport


class CatalogReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_evaluation_run(
        self,
        report: EvaluationReport,
        created_by: UUID | None = None,
    ) -> CatalogEvaluationRun:
        """Persists an immutable evaluation report into catalog_evaluation_runs."""
        # Convert metric results to dict
        metrics_dict = {k: v.model_dump(mode="json") for k, v in report.metric_results.items()}
        detailed_dict = {
            "usable_breakdown": report.usable_product_breakdown.model_dump(mode="json"),
            "release_decision": report.release_decision,
            "blockers": report.blockers,
            "evidence_references": report.evidence_references,
        }

        db_run = CatalogEvaluationRun(
            id=report.evaluation_id,
            configuration_version=report.configuration_version,
            status=report.status,
            all_passed=report.all_passed,
            metrics_summary=metrics_dict,
            detailed_report=detailed_dict,
            created_by=created_by,
            started_at=report.started_at,
            completed_at=report.completed_at,
        )
        self.session.add(db_run)
        await self.session.commit()
        await self.session.refresh(db_run)
        return db_run

    async def get_evaluation(self, evaluation_id: UUID) -> CatalogEvaluationRun | None:
        """Retrieve historical evaluation run by its ID."""
        return await self.session.get(CatalogEvaluationRun, evaluation_id)

    async def get_latest_evaluation(self) -> CatalogEvaluationRun | None:
        """Retrieve the most recent evaluation run."""
        query = (
            select(CatalogEvaluationRun).order_by(desc(CatalogEvaluationRun.created_at)).limit(1)
        )
        return await self.session.scalar(query)

    async def list_evaluations(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CatalogEvaluationRun]:
        """List historical evaluation runs ordered by creation timestamp."""
        query = (
            select(CatalogEvaluationRun)
            .order_by(desc(CatalogEvaluationRun.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
