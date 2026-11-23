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
from fashx.catalog.errors import PermissionDeniedError


class CatalogAuthorizationGuard:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.auth_service = CatalogAuthorizationService(session)

    async def guard(
        self,
        source_id: UUID,
        operation: CatalogPermissionCode | str,
        product_id: str | None = None,
        category: str | None = None,
        market: str | None = None,
        processor_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AuthorizationDecisionResponse:
        op_str = operation.value if isinstance(operation, CatalogPermissionCode) else str(operation)
        context = AuthorizationContext(
            source_id=source_id,
            operation=op_str,
            product_id=product_id,
            category=category,
            market=market,
            processor_id=processor_id,
            correlation_id=correlation_id,
        )
        decision = await self.auth_service.evaluate(context)
        if decision.decision != "ALLOW":
            raise PermissionDeniedError(
                reason_code=decision.reason_code,
                message=f"Catalog authorization denied for operation '{op_str}': {decision.reason_code}",
            )
        return decision

    async def guard_product_read(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.PRODUCT_DATA_READ, **kwargs)

    async def guard_product_store(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.PRODUCT_DATA_STORE, **kwargs)

    async def guard_product_display(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.PRODUCT_DISPLAY, **kwargs)

    async def guard_image_fetch(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.IMAGE_FETCH, **kwargs)

    async def guard_image_store(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.IMAGE_STORE, **kwargs)

    async def guard_image_display(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.IMAGE_DISPLAY, **kwargs)

    async def guard_image_ai_process(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.IMAGE_AI_PROCESS, **kwargs)

    async def guard_vto_process(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.VTO_PROCESS, **kwargs)

    async def guard_derivative_create(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.DERIVATIVE_CREATE, **kwargs)

    async def guard_merchant_redirect(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.MERCHANT_REDIRECT, **kwargs)

    async def guard_affiliate_attribution(
        self, source_id: UUID, **kwargs: Any
    ) -> AuthorizationDecisionResponse:
        return await self.guard(source_id, CatalogPermissionCode.AFFILIATE_ATTRIBUTION, **kwargs)
