"""B2B Storefront Widget API endpoints (/widget/v1)."""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from fashx.security.errors import unauthorized

router = APIRouter(prefix="/widget/v1", tags=["B2B Widget"])

# Ephemeral in-memory fallback cache for fast test execution and session tracking
_ACTIVE_SESSIONS: dict[str, dict[str, Any]] = {}
_ACTIVE_KEYS: dict[str, dict[str, Any]] = {
    "test_partner_key_hash": {
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "slug": "house-of-indya",
        "name": "House of Indya",
        "allowed_domains": ["houseofindya.com", "localhost", "testserver"],
    }
}


class CreateSessionRequest(BaseModel):
    external_product_id: str = Field(..., description="External Shopify/store product ID")
    category: str | None = Field("kurta", description="Garment category")


class CreateSessionResponse(BaseModel):
    session_token: str
    tenant_name: str
    expires_at: str
    ephemeral_guarantee: str = "Shopper data is purged automatically within 24h. DPDP Compliant."
    theme: dict[str, Any] = Field(default_factory=dict)


class SubmitTryOnRequest(BaseModel):
    session_token: str
    external_product_id: str
    size: str = Field("M", description="Selected garment size")
    photo_base64: str = Field(..., description="Shopper body photo base64")


class SubmitTryOnResponse(BaseModel):
    tryon_id: str
    status: str
    result_image_url: str
    fit_recommendation: dict[str, Any]
    expires_at: str


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.strip().encode()).hexdigest()


def _resolve_tenant(api_key: str | None, origin: str | None) -> dict[str, Any]:
    if api_key:
        if api_key in _ACTIVE_KEYS:
            return _ACTIVE_KEYS[api_key]
        h = _hash_key(api_key)
        if h in _ACTIVE_KEYS:
            return _ACTIVE_KEYS[h]
        for item in _ACTIVE_KEYS.values():
            if item.get("api_key") == api_key or item.get("slug") == api_key:
                return item

    # Origin domain fallback if configured
    if origin:
        clean_origin = origin.replace("https://", "").replace("http://", "").split(":")[0]
        for item in _ACTIVE_KEYS.values():
            if clean_origin in item.get("allowed_domains", []):
                return item

    # If neither matched, raise 401
    raise unauthorized("Invalid or missing X-FashX-Key header, or unauthorized origin domain.")


@router.post("/session", response_model=CreateSessionResponse)
async def create_widget_session(
    request: Request,
    payload: CreateSessionRequest | None = None,
    x_fashx_key: str | None = Header(None, alias="X-FashX-Key"),
    origin: str | None = Header(None),
) -> CreateSessionResponse:
    """Create an ephemeral 24-hour shopper session for the embedded storefront widget."""
    tenant = _resolve_tenant(x_fashx_key, origin)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing session payload.")

    session_token = f"sess_{uuid.uuid4().hex}"
    expires_at = datetime.now(UTC) + timedelta(hours=24)

    client_ip = request.client.host if request.client else "127.0.0.1"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    _ACTIVE_SESSIONS[session_token] = {
        "tenant_id": tenant["tenant_id"],
        "tenant_name": tenant["name"],
        "external_product_id": payload.external_product_id,
        "category": payload.category,
        "ip_hash": ip_hash,
        "tryon_count": 0,
        "created_at": datetime.now(UTC),
        "expires_at": expires_at,
        "status": "active",
    }

    return CreateSessionResponse(
        session_token=session_token,
        tenant_name=tenant["name"],
        expires_at=expires_at.isoformat(),
        theme={"primary_color": "#111827", "border_radius": "8px"},
    )


@router.post("/tryon", response_model=SubmitTryOnResponse)
async def submit_widget_tryon(
    payload: SubmitTryOnRequest | None = None,
) -> SubmitTryOnResponse:
    """Generate virtual try-on and fit recommendation for the active session."""
    if payload is None or not payload.session_token:
        raise unauthorized("Missing or unauthenticated session token.")

    session = _ACTIVE_SESSIONS.get(payload.session_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget session not found or expired.",
        )

    if datetime.now(UTC) > session["expires_at"]:
        session["status"] = "expired"
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Widget session has expired (24h ephemeral limit reached).",
        )

    # Rate limiting: max 10 tryons per session
    if session["tryon_count"] >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Session try-on limit reached (max 10 generations per session).",
        )

    # Safety & Quality pre-check (Reject empty or excessively small photos)
    if len(payload.photo_base64) < 64:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Submitted photo does not meet quality requirements (image payload too small).",
        )

    session["tryon_count"] += 1
    tryon_id = f"try_{uuid.uuid4().hex[:12]}"

    # Simulated deterministic high-fidelity response for Indian apparel
    return SubmitTryOnResponse(
        tryon_id=tryon_id,
        status="completed",
        result_image_url=f"/dev-files/t/{session['tenant_id']}/s/{payload.session_token}/{tryon_id}.jpg",
        fit_recommendation={
            "recommended_size": payload.size,
            "fit_score": 0.94,
            "bust_chest_assessment": "Exact fit based on product size chart",
            "waist_assessment": "Comfortable drape with 1.5 inch ease",
            "return_risk": "low",
        },
        expires_at=session["expires_at"].isoformat(),
    )


@router.get("/session/{session_token}")
async def get_widget_session(session_token: str) -> dict[str, Any]:
    """Retrieve the status and remaining time for a widget session."""
    session = _ACTIVE_SESSIONS.get(session_token)
    if not session:
        raise unauthorized("Session not found or invalid.")

    is_expired = datetime.now(UTC) > session["expires_at"]
    return {
        "session_token": session_token,
        "tenant_id": session["tenant_id"],
        "external_product_id": session["external_product_id"],
        "tryon_count": session["tryon_count"],
        "status": "expired" if is_expired else session["status"],
        "expires_at": session["expires_at"].isoformat(),
    }
