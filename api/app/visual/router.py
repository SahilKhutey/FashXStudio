"""FastAPI Router for FashXStudio Visual Layer Architecture.

Exposes endpoints for Screen Inventory, Device Breakpoints, and Domain Hierarchy.
Adheres to Rule I01 (Layer Separation) and Rule I19 (Standardized Error Envelopes).
"""

from fastapi import APIRouter, HTTPException, Query, status

from api.app.core.errors import EntityNotFoundError
from schemas.visual.v1 import (
    BreakpointConfig,
    DeviceBreakpoint,
    ScreenDefinition,
    ScreenDomain,
    ScreenInventoryRegistry,
)
from .catalog import BREAKPOINT_CONFIGS, get_screen_inventory

router = APIRouter(prefix="/visual", tags=["Visual Architecture"])


@router.get(
    "/screens",
    response_model=ScreenInventoryRegistry,
    summary="Get complete screen inventory",
)
def list_screens(
    domain: ScreenDomain | None = Query(default=None, description="Filter by domain"),
    requires_auth: bool | None = Query(default=None, description="Filter by auth requirement"),
) -> ScreenInventoryRegistry:
    inventory = get_screen_inventory()
    filtered = inventory.screens
    if domain is not None:
        filtered = [s for s in filtered if s.domain == domain]
    if requires_auth is not None:
        filtered = [s for s in filtered if s.requires_auth == requires_auth]
    return ScreenInventoryRegistry(
        version=inventory.version,
        total_screens=len(filtered),
        screens=filtered,
    )


@router.get(
    "/screens/{screen_id}",
    response_model=ScreenDefinition,
    summary="Get screen details by ID",
)
def get_screen(screen_id: str) -> ScreenDefinition:
    inventory = get_screen_inventory()
    screen = inventory.get_screen(screen_id)
    if screen is None:
        raise EntityNotFoundError("Screen", screen_id)
    return screen


@router.get(
    "/breakpoints",
    response_model=list[BreakpointConfig],
    summary="Get responsive device breakpoint configurations",
)
def list_breakpoints() -> list[BreakpointConfig]:
    return BREAKPOINT_CONFIGS


@router.get(
    "/domains",
    summary="Get domain summary",
)
def get_domain_summary() -> dict[str, int]:
    inventory = get_screen_inventory()
    summary: dict[str, int] = {}
    for screen in inventory.screens:
        summary[screen.domain] = summary.get(screen.domain, 0) + 1
    return summary
