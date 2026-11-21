from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_operations import (
    ErrorCategory,
    FailedStage,
    IngestRunError,
)
from fashx.catalog.operations.schemas import (
    IngestErrorListResponse,
    IngestRunErrorResponse,
)

# Common regex patterns for tokens, keys, passwords, bearer tokens
SENSITIVE_PATTERNS = [
    re.compile(r"(Bearer\s+)[A-Za-z0-9_\-\.]{8,}", re.IGNORECASE),
    re.compile(r"(api[_\-]?key[:=]\s*['\"]?)[A-Za-z0-9_\-]{8,}(['\"]?)", re.IGNORECASE),
    re.compile(r"(token[:=]\s*['\"]?)[A-Za-z0-9_\-]{8,}(['\"]?)", re.IGNORECASE),
    re.compile(r"(password[:=]\s*['\"]?)[^\s'\"]+(['\"]?)", re.IGNORECASE),
    re.compile(r"(secret[:=]\s*['\"]?)[^\s'\"]+(['\"]?)", re.IGNORECASE),
]


def redact_sensitive_error_message(message: str) -> str:
    redacted = message
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(r"\1******\2" if pattern.groups == 2 else r"\1******", redacted)
    return redacted


class IngestionReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_error(
        self,
        *,
        ingest_run_id: UUID,
        source_id: UUID,
        merchant_id: UUID | None,
        error_code: str,
        error_category: str = ErrorCategory.INTERNAL.value,
        failed_stage: str = FailedStage.FETCH.value,
        raw_error_message: str,
        source_product_reference: str | None = None,
        retryable: bool = False,
        attempt_number: int = 1,
    ) -> IngestRunError:
        safe_msg = redact_sensitive_error_message(raw_error_message)
        error = IngestRunError(
            ingest_run_id=ingest_run_id,
            source_id=source_id,
            merchant_id=merchant_id,
            error_code=error_code,
            error_category=error_category,
            failed_stage=failed_stage,
            source_product_reference=source_product_reference,
            safe_error_message=safe_msg,
            retryable=retryable,
            attempt_number=attempt_number,
        )
        self.session.add(error)
        await self.session.commit()
        await self.session.refresh(error)
        return error

    async def get_errors(
        self,
        *,
        source_id: UUID | None = None,
        run_id: UUID | None = None,
        merchant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> IngestErrorListResponse:
        query = select(IngestRunError)
        if source_id:
            query = query.where(IngestRunError.source_id == source_id)
        if run_id:
            query = query.where(IngestRunError.ingest_run_id == run_id)
        if merchant_id:
            query = query.where(IngestRunError.merchant_id == merchant_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0

        offset = max(0, (page - 1) * page_size)
        query = query.order_by(desc(IngestRunError.occurred_at)).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        errors = [IngestRunErrorResponse.model_validate(e) for e in result.scalars().all()]

        return IngestErrorListResponse(
            errors=errors,
            total_count=total,
            page=page,
            page_size=page_size,
        )
