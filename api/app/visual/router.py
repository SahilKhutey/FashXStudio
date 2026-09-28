"""FastAPI Router for FashXStudio Visual Layer Architecture & Design Tokens.

Exposes endpoints for Screen Inventory, Templates, Dependency Groups, Breakpoints, Domains,
and the Design Token System (Primitives, Semantic Themes, MST, Components, WCAG Validation).
Adheres to Rule I01 (Layer Separation) and Rule I19 (Standardized Error Envelopes).
"""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from api.app.core.errors import EntityNotFoundError
from schemas.visual.v1 import (
    BreakpointConfig,
    DeviceBreakpoint,
    ImplementationDependencyGroup,
    PageTemplateType,
    ScreenDefinition,
    ScreenDomain,
    ScreenInventoryRegistry,
)
from schemas.visual.tokens import (
    DesignTokenRegistry,
    MonkSkinTonePalette,
    ThemeMode,
    ThemeTokens,
    TokenValidationReport,
)
from .catalog import BREAKPOINT_CONFIGS, get_screen_inventory
from .tokens_service import (
    calculate_adaptive_columns,
    get_theme_tokens,
    get_token_registry,
    validate_tokens,
)

router = APIRouter(prefix="/visual", tags=["Visual Architecture"])


# ---------------------------------------------------------------------------
# Screen Inventory & Layout Architecture Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/screens",
    response_model=ScreenInventoryRegistry,
    summary="Get complete screen inventory",
)
def list_screens(
    domain: ScreenDomain | None = Query(default=None, description="Filter by domain"),
    template_type: PageTemplateType | None = Query(default=None, description="Filter by template"),
    dependency_group: ImplementationDependencyGroup | None = Query(default=None, description="Filter by group"),
    requires_auth: bool | None = Query(default=None, description="Filter by auth requirement"),
) -> ScreenInventoryRegistry:
    inventory = get_screen_inventory()
    filtered = inventory.screens
    if domain is not None:
        filtered = [s for s in filtered if s.domain == domain]
    if template_type is not None:
        filtered = [s for s in filtered if s.template_type == template_type]
    if dependency_group is not None:
        filtered = [s for s in filtered if s.dependency_group == dependency_group]
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
    summary="Get screen details by ID or Code",
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


@router.get(
    "/templates",
    summary="Get screen count by page template",
)
def get_template_summary() -> dict[str, int]:
    inventory = get_screen_inventory()
    summary: dict[str, int] = {}
    for screen in inventory.screens:
        t = str(screen.template_type)
        summary[t] = summary.get(t, 0) + 1
    return summary


@router.get(
    "/dependency-groups",
    summary="Get screen count by dependency group",
)
def get_dependency_group_summary() -> dict[str, int]:
    inventory = get_screen_inventory()
    summary: dict[str, int] = {}
    for screen in inventory.screens:
        g = str(screen.dependency_group)
        summary[g] = summary.get(g, 0) + 1
    return summary


# ---------------------------------------------------------------------------
# Design Token System Endpoints (Phase 02)
# ---------------------------------------------------------------------------

@router.get(
    "/tokens",
    response_model=DesignTokenRegistry,
    summary="Get full design token registry",
)
def get_tokens() -> DesignTokenRegistry:
    """Return the frozen master design token registry containing all scales."""
    return get_token_registry()


@router.get(
    "/tokens/theme",
    response_model=ThemeTokens,
    summary="Get theme-resolved semantic tokens",
)
def get_theme(
    mode: ThemeMode = Query(default=ThemeMode.LIGHT, description="Theme mode (light or dark)"),
) -> ThemeTokens:
    """Resolve semantic surface, content, border, action, and status tokens for the given mode."""
    return get_theme_tokens(mode=mode)


@router.get(
    "/tokens/skin-tones",
    response_model=MonkSkinTonePalette,
    summary="Get Monk Skin Tone 10-point scale and undertones",
)
def get_skin_tones() -> MonkSkinTonePalette:
    """Return the Monk Skin Tone (MST) 10-point scale and undertone calibration values."""
    return get_token_registry().monk_skin_tones


@router.get(
    "/tokens/components/{component_name}",
    summary="Get component-specific token bindings",
)
def get_component_tokens(component_name: str) -> dict[str, Any]:
    """Retrieve pre-bound component tokens (e.g. product-card, fashion-card)."""
    registry = get_token_registry()
    name_clean = component_name.lower().replace("_", "-")
    if name_clean in ["product-card", "productcard"]:
        return registry.product_card_tokens.model_dump()
    elif name_clean in ["fashion-card", "fashioncard"]:
        return registry.fashion_card_tokens.model_dump()
    else:
        raise EntityNotFoundError("ComponentTokens", component_name)


@router.post(
    "/tokens/validate",
    response_model=TokenValidationReport,
    summary="Run automated token integrity and WCAG 2.2 contrast validation",
)
def run_token_validation() -> TokenValidationReport:
    """Execute WCAG 2.2 contrast calculations and check for broken token references."""
    return validate_tokens()


@router.get(
    "/tokens/grid-calculator",
    summary="Calculate adaptive grid columns based on container width",
)
def calculate_grid(
    container_width_px: int = Query(..., ge=1, description="Available container width in pixels"),
    min_card_width_px: int = Query(default=240, ge=50, description="Minimum card width in pixels"),
    gutter_px: int = Query(default=16, ge=0, description="Gutter spacing in pixels"),
    max_columns: int = Query(default=12, ge=1, le=24, description="Maximum allowed columns"),
) -> dict[str, int]:
    """Compute adaptive column count for dynamic product and fashion grids (Section 2.25)."""
    columns = calculate_adaptive_columns(
        container_width_px=container_width_px,
        min_card_width_px=min_card_width_px,
        gutter_px=gutter_px,
        max_columns=max_columns,
    )
    return {
        "container_width_px": container_width_px,
        "min_card_width_px": min_card_width_px,
        "gutter_px": gutter_px,
        "columns": columns,
    }
