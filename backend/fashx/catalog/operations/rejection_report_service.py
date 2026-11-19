from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog import CatalogSource
from database.models.catalog_sync import CatalogIngestionQuarantine
from fashx.catalog.errors import CatalogAuthorizationError
from fashx.catalog.operations.schemas import (
    QuarantinedProductResponse,
    QuarantineReportListResponse,
    QuarantineResolutionGuidance,
)

RESOLUTION_GUIDANCE_MAP: dict[str, tuple[str, str, str]] = {
    "MISSING_FIELD": (
        "BLOCKING",
        "A mandatory product field is missing.",
        "Ensure the missing field is provided in the feed or configure a default value.",
    ),
    "INVALID_URL": (
        "BLOCKING",
        "Product URL is invalid or insecure.",
        "Ensure the product URL is a fully-qualified, reachable HTTPS link.",
    ),
    "PRICE_NON_POSITIVE": (
        "BLOCKING",
        "Price must be greater than zero.",
        "Verify that price_minor is a positive number representing the retail price in minor currency units.",
    ),
    "TITLE_TOO_SHORT": (
        "WARNING",
        "Product title does not meet length criteria.",
        "Provide a descriptive product title with at least 3 characters.",
    ),
    "CATEGORY_UNMAPPED": (
        "WARNING",
        "Source category does not match canonical taxonomy.",
        "Add a taxonomy category mapping in CategoryMap or update the source feed category.",
    ),
    "UNAUTHORIZED_SOURCE": (
        "BLOCKING",
        "Source does not possess valid authorization evidence.",
        "Submit current license or distribution agreement evidence to platform administration.",
    ),
}


def get_resolution_guidance(
    reason_code: str, field_name: str | None
) -> QuarantineResolutionGuidance:
    normalized_reason = reason_code.upper()
    for key, (severity, summary, action) in RESOLUTION_GUIDANCE_MAP.items():
        if key in normalized_reason:
            if field_name and "{field_name}" in action:
                action = action.replace("{field_name}", field_name)
            return QuarantineResolutionGuidance(
                reason_code=reason_code,
                severity=severity,
                summary=summary,
                recommended_action=action,
            )
    return QuarantineResolutionGuidance(
        reason_code=reason_code,
        severity="WARNING",
        summary=f"Validation failed with code: {reason_code}",
        recommended_action="Inspect the safe record reference payload and update the merchant source feed accordingly.",
    )


class RejectionReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_rejection_report(
        self,
        source_id: UUID,
        status: str | None = None,
        merchant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> QuarantineReportListResponse:
        source = await self.session.get(CatalogSource, source_id)
        if not source:
            raise CatalogAuthorizationError(
                f"Catalog source '{source_id}' not found.",
                code="source_not_found",
            )
        if merchant_id and source.merchant_id != merchant_id:
            raise CatalogAuthorizationError(
                f"Access denied: source does not belong to merchant '{merchant_id}'.",
                code="tenant_isolation_violation",
            )

        query = select(CatalogIngestionQuarantine).where(
            CatalogIngestionQuarantine.source_id == source_id
        )
        if status:
            query = query.where(CatalogIngestionQuarantine.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0

        query = (
            query.order_by(desc(CatalogIngestionQuarantine.first_seen_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = result.scalars().all()

        records = [
            QuarantinedProductResponse(
                id=item.id,
                source_id=item.source_id,
                ingest_run_id=item.ingest_run_id,
                source_product_id=item.source_product_id,
                reason_code=item.reason_code,
                field_name=item.field_name,
                guidance=get_resolution_guidance(item.reason_code, item.field_name),
                first_seen_at=item.first_seen_at,
                status=item.status,
            )
            for item in items
        ]

        return QuarantineReportListResponse(
            records=records,
            total_count=total,
        )
