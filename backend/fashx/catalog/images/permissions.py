from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.catalog_auth import CatalogPermissionCode
from fashx.catalog.authorization.schemas import (
    AuthorizationContext,
    AuthorizationDecisionResponse,
)
from fashx.catalog.authorization.service import CatalogAuthorizationService
from fashx.catalog.images.models import ImageOperation, PermissionDecision


class ImagePermissionDenied(Exception):
    """Raised when an image operation is refused by the authorization engine."""

    def __init__(self, reason: str, source_id: UUID, operation: str) -> None:
        super().__init__(
            f"Image permission denied for '{operation}' on source {source_id}: {reason}"
        )
        self.reason = reason
        self.source_id = source_id
        self.operation = operation


class ImagePermissionService:
    """Evaluates operation-specific permissions with fail-closed semantics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.auth_service = CatalogAuthorizationService(session)

    async def evaluate(
        self,
        source_id: UUID,
        operation: ImageOperation | CatalogPermissionCode | str,
        category: str | None = None,
        correlation_id: str | None = None,
        processor_id: str | None = None,
        **kwargs: Any,
    ) -> PermissionDecision:
        op_str = operation.value if hasattr(operation, "value") else str(operation)
        try:
            context = AuthorizationContext(
                source_id=source_id,
                operation=op_str,
                category=category,
                processor_id=processor_id,
                correlation_id=correlation_id,
            )
            resp: AuthorizationDecisionResponse = await self.auth_service.evaluate(context)
            allowed = resp.decision == "ALLOW"
            return PermissionDecision(
                allowed=allowed,
                source_id=source_id,
                evidence_id=resp.permission_id,
                revision=1,
                policy_version="v1",
                reason=resp.reason_code if not allowed else None,
            )
        except Exception as exc:
            # Fail closed on any exception or database/service failure
            return PermissionDecision(
                allowed=False,
                source_id=source_id,
                evidence_id=None,
                revision=None,
                policy_version="v1",
                reason=f"fail_closed_error: {exc}",
            )

    async def require(
        self,
        source_id: UUID,
        operation: ImageOperation | CatalogPermissionCode | str,
        category: str | None = None,
        correlation_id: str | None = None,
        processor_id: str | None = None,
        **kwargs: Any,
    ) -> PermissionDecision:
        decision = await self.evaluate(
            source_id=source_id,
            operation=operation,
            category=category,
            correlation_id=correlation_id,
            processor_id=processor_id,
            **kwargs,
        )
        if not decision.allowed:
            op_str = operation.value if hasattr(operation, "value") else str(operation)
            raise ImagePermissionDenied(
                reason=decision.reason or "permission_denied",
                source_id=source_id,
                operation=op_str,
            )
        return decision
