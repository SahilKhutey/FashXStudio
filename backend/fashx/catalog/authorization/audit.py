from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_auth import CatalogAuthorizationDecision
from fashx.catalog.authorization.evaluator import EvaluationResult
from fashx.catalog.authorization.repository import CatalogAuthorizationDecisionRepository
from fashx.catalog.authorization.schemas import AuthorizationContext


async def log_authorization_decision(
    session: AsyncSession,
    context: AuthorizationContext,
    result: EvaluationResult,
    evaluated_at: datetime | None = None,
) -> CatalogAuthorizationDecision:
    if evaluated_at is None:
        evaluated_at = datetime.now(UTC)

    repo = CatalogAuthorizationDecisionRepository(session)
    decision = CatalogAuthorizationDecision(
        source_id=context.source_id,
        product_id=context.product_id,
        operation=context.operation,
        decision=result.decision,
        reason_code=result.reason_code,
        permission_id=result.permission_id,
        processor_id=context.processor_id,
        market=context.market,
        category=context.category,
        correlation_id=context.correlation_id,
        evaluated_at=evaluated_at,
    )
    return await repo.create(decision)
