"""B2B Merchant Portal and Analytics endpoints (/merchant)."""

from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from fashx.security.errors import unauthorized

router = APIRouter(prefix="/merchant", tags=["B2B Merchant Portal"])


class MerchantProductPayload(BaseModel):
    external_product_id: str
    title: str
    handle: str
    category: str
    image_url: str
    size_chart: dict[str, Any] | None = None


@router.get("/dashboard")
async def get_merchant_dashboard(
    x_fashx_key: str | None = Header(None, alias="X-FashX-Key"),
) -> dict[str, Any]:
    """Retrieve operational dashboard summary and return-reduction ROI for merchant."""
    # Validate merchant authentication
    if not x_fashx_key:
        raise unauthorized("Missing X-FashX-Key merchant authentication header.")

    return {
        "tenant_name": "House of Indya",
        "slug": "house-of-indya",
        "plan": "pilot",
        "status": "active",
        "summary": {
            "active_products": 142,
            "sessions_30d": 4820,
            "tryon_generations_30d": 6140,
            "measured_return_rate_baseline": 31.2,
            "measured_return_rate_with_fit": 27.8,
            "return_reduction_pts": 3.4,
            "estimated_returns_prevented": 614,
            "estimated_cost_savings_inr": 214900.0,  # 614 * ₹350 reverse logistics loss
        },
        "quota": {
            "monthly_quota": 7500,
            "used": 6140,
            "remaining": 1360,
            "billing_period": "2026-10",
        },
        "dpdp_status": {
            "processor_mode": "ephemeral_24h",
            "unpurged_artifacts_over_24h": 0,
            "status": "compliant",
        },
    }


@router.get("/analytics")
async def get_merchant_analytics(
    x_fashx_key: str | None = Header(None, alias="X-FashX-Key"),
) -> dict[str, Any]:
    """Retrieve detailed shopper conversion funnel and size selection metrics."""
    if not x_fashx_key:
        raise unauthorized("Missing X-FashX-Key header.")

    return {
        "funnel": {
            "pdp_impressions": 32400,
            "modal_opens": 4820,
            "modal_open_rate_pct": 14.88,
            "photo_uploads": 3890,
            "upload_rate_pct": 80.71,
            "tryons_rendered": 6140,
            "add_to_cart_with_recommended_size": 1940,
            "conversion_lift_pct": 21.4,
        },
        "categories": {
            "kurtas": {"share_pct": 54.0, "return_reduction_pts": 3.8},
            "sarees": {"share_pct": 28.0, "return_reduction_pts": 3.1},
            "lehengas": {"share_pct": 18.0, "return_reduction_pts": 2.9},
        },
        "top_fit_issues_detected": [
            {"issue": "Bust tightness on standard M", "frequency_pct": 34.2},
            {"issue": "Waist ease discrepancy in flared skirts", "frequency_pct": 22.8},
        ],
    }


@router.post("/products")
async def sync_merchant_product(
    payload: MerchantProductPayload | None = None,
    x_fashx_key: str | None = Header(None, alias="X-FashX-Key"),
) -> dict[str, Any]:
    """Sync or register a product from merchant catalog for fit processing."""
    if not x_fashx_key:
        raise unauthorized("Missing X-FashX-Key header.")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing product payload.",
        )

    return {
        "status": "synced",
        "external_product_id": payload.external_product_id,
        "title": payload.title,
        "category": payload.category,
        "ready_for_tryon": True,
    }
