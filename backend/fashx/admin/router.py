from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from database.models.feature_flags import FeatureFlag
from fashx.core.database import get_db_session
from fashx.core.flags import is_flag_enabled, set_flag
from fashx.security.deps import require_role
from fashx.security.tokens import Claims

router = APIRouter(prefix="/admin", tags=["admin"])


class FeatureFlagUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="Feature flag identifier")
    enabled: bool = Field(..., description="Target state")
    reason: str = Field(..., min_length=3, max_length=500, description="Mandatory audit justification")


class FeatureFlagResponse(BaseModel):
    name: str
    enabled: bool
    description: str | None = None
    updated_at: str | None = None
    updated_by: str | None = None
    reason: str | None = None


@router.get("/feature-flags", response_model=list[FeatureFlagResponse])
async def list_feature_flags(
    principal: Any = Depends(require_role("admin")),
) -> list[FeatureFlagResponse]:
    """List all dynamic kill switches and feature flags."""
    async for session in get_db_session():
        stmt = select(FeatureFlag).order_by(FeatureFlag.name)
        res = await session.execute(stmt)
        flags = res.scalars().all()
        return [
            FeatureFlagResponse(
                name=f.name,
                enabled=f.enabled,
                description=f.description,
                updated_at=f.updated_at.isoformat() if f.updated_at else None,
                updated_by=f.updated_by,
                reason=f.reason,
            )
            for f in flags
        ]
    return []


@router.post("/feature-flags")
async def update_feature_flag(
    payload: FeatureFlagUpdateRequest,
    principal: Any = Depends(require_role("admin")),
) -> dict[str, Any]:
    """Toggle a feature flag / kill switch with audit attribution (Rule 9.10)."""
    actor = getattr(principal, "user_id", "admin")
    await set_flag(
        flag_name=payload.name,
        enabled=payload.enabled,
        updated_by=str(actor),
        reason=payload.reason,
    )
    return {
        "name": payload.name,
        "enabled": payload.enabled,
        "updated_by": str(actor),
        "status": "updated",
    }
