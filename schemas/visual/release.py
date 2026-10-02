"""FashXStudio Production Visual Integration, Verification, Validation & Release Framework Contracts — Version 1.

Defines the production layer model (Layers 0-8), screen and navigation registries,
design token validation, release gates, visual quality checklists, golden artifacts,
and E2E journey verification contracts for Phase 16 (VD-16 — FINAL).
Adheres strictly to Constitution Rule I02 (Contract Primacy) with extra="forbid".
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProductionLayer(StrEnum):
    """Production 9-layer architectural model (Section 16.4)."""
    LAYER_0_PLATFORM = "layer_0_platform"            # Platform, browser, viewport
    LAYER_1_APPLICATION_SHELL = "layer_1_shell"      # Shell, layout, providers, global navigation
    LAYER_2_DESIGN_SYSTEM = "layer_2_design_system"  # Tokens, primitives, core components
    LAYER_3_FEATURE_SYSTEMS = "layer_3_features"     # Shopping, Discovery, Styling, Maps, AI, Profile
    LAYER_4_TEMPLATES = "layer_4_templates"          # 11 reusable page templates
    LAYER_5_SCREENS = "layer_5_screens"              # Concrete screens and pages
    LAYER_6_DATA_SERVICES = "layer_6_services"       # Domain services, adapters, view-models
    LAYER_7_ANALYTICS = "layer_7_analytics"          # Telemetry, observability, metrics
    LAYER_8_QA_VALIDATION = "layer_8_qa"             # Visual regression, a11y gates, release verification


class ReleaseGateStatus(StrEnum):
    """Status classification for production release gates (Section 16.56)."""
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    WARNING = "warning"
    BLOCKED = "blocked"


class ReleaseEnvironment(StrEnum):
    """Deployment targets for visual validation (Section 16.50)."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class QualityCategory(StrEnum):
    """Categories in the Master Visual Quality Checklist (Section 16.57)."""
    FOUNDATION = "foundation"
    SHELL = "shell"
    COMPONENTS = "components"
    FASHION = "fashion"
    SHOPPING = "shopping"
    DISCOVERY = "discovery"
    STYLING = "styling"
    GEOGRAPHY = "geography"
    AI = "ai"
    PERSONAL = "personal"
    RESPONSIVE = "responsive"
    ACCESSIBILITY = "accessibility"
    QA = "qa"


class GoldenArtifactType(StrEnum):
    """Classification of golden baseline regression targets (Section 16.38 & 16.39)."""
    SCREEN = "screen"
    COMPONENT = "component"


# ---------------------------------------------------------------------------
# Screen & Navigation Registry Contracts
# ---------------------------------------------------------------------------

class ScreenRegistryEntryContract(BaseContractModel):
    """Centralized metadata specification for a registered screen (Section 16.14)."""
    screen_id: str = Field(..., description="Screen inventory ID e.g. D01, P01, AI01")
    route: str = Field(..., description="Canonical URI path")
    title: str = Field(..., description="Human-readable title")
    template: str = Field(..., description="Template ID e.g. T01_GRID, T04_SPLIT")
    feature: str = Field(..., description="Feature domain e.g. shopping, ai, styling")
    accessibility_role: str = Field(default="main", description="ARIA landmark role")
    analytics_tag: str = Field(..., description="Telemetry screen identifier")
    dependencies: list[str] = Field(default_factory=list, description="Required component and token IDs")
    is_production_ready: bool = Field(default=True)


class NavigationRegistryEntryContract(BaseContractModel):
    """Centralized production navigation registry entry (Section 16.13)."""
    route: str = Field(..., description="Target URI route")
    label: str = Field(..., description="User-facing navigation label")
    icon: str = Field(..., description="Icon identifier from token set")
    group: str = Field(..., description="primary, secondary, profile, or footer")
    visibility: str = Field(default="public", description="public, authenticated, or admin")
    permissions: list[str] = Field(default_factory=list)
    screen_id: str = Field(..., description="Associated screen ID")


# ---------------------------------------------------------------------------
# Design Token Validation Contracts
# ---------------------------------------------------------------------------

class TokenValidationRequestContract(BaseContractModel):
    """Payload to validate token references and prevent rogue values (Section 16.10 & 16.11)."""
    token_name: str = Field(..., description="Token identifier e.g. color.primary.text")
    token_category: str = Field(..., description="color, typography, spacing, radius, shadow, motion")
    primitive_ref: str = Field(..., description="Primitive reference e.g. gray-900, 16px, 4px")
    semantic_usage: str = Field(..., description="Intended semantic context")
    theme: str = Field(default="light", description="light or dark theme")


class TokenValidationReportContract(BaseContractModel):
    """Validation report confirming token reference integrity (Section 16.11)."""
    token_name: str
    is_valid: bool
    resolved_value: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    hierarchy_valid: bool = Field(default=True, description="Screen -> Component -> Semantic -> Primitive verified")


# ---------------------------------------------------------------------------
# Release Gate & Audit Contracts
# ---------------------------------------------------------------------------

class ReleaseGateResultContract(BaseContractModel):
    """Evaluation result for an individual release gate (Section 16.56)."""
    gate_name: str = Field(..., description="functional, visual, a11y, performance, integration")
    status: ReleaseGateStatus
    score: float = Field(..., ge=0.0, le=100.0, description="Compliance score percentage")
    passed: bool
    violations: list[str] = Field(default_factory=list)
    timestamp: str = Field(..., description="ISO 8601 evaluation timestamp")


class VisualReleaseGateAuditRequest(BaseContractModel):
    """Input payload to execute the comprehensive production release gate audit (Section 16.56)."""
    release_version: str = Field(..., description="Target release tag e.g. v1.0.0-rc1")
    environment: ReleaseEnvironment = Field(default=ReleaseEnvironment.STAGING)
    target_screens: list[str] = Field(default_factory=list, description="Target screens to audit; empty for all")
    include_e2e: bool = Field(default=True)
    include_a11y: bool = Field(default=True)


class VisualChecklistItemContract(BaseContractModel):
    """Item specification in the Master Visual Quality Checklist (Section 16.57)."""
    item_id: str = Field(..., description="Unique checklist identifier e.g. CHK-FOUNDATION-01")
    category: QualityCategory
    title: str = Field(..., description="Short checklist title")
    description: str = Field(..., description="Verification criteria")
    is_verified: bool = Field(default=True)
    verification_method: str = Field(default="automated_test", description="automated_test, visual_diff, or manual_qa")


class EndToEndJourneySpecContract(BaseContractModel):
    """Specification and verification result for Master E2E User Journeys (Section 16.36)."""
    journey_id: str = Field(..., description="E2E-001 through E2E-005")
    name: str = Field(..., description="Journey name")
    steps: list[str] = Field(..., description="Ordered progression of journey interactions")
    status: ReleaseGateStatus = Field(default=ReleaseGateStatus.PASSED)
    verified_at: str = Field(..., description="ISO 8601 timestamp")


class GoldenArtifactContract(BaseContractModel):
    """Golden screenshot or component baseline anchor (Section 16.38 & 16.39)."""
    id: str = Field(..., description="Unique anchor ID e.g. GOLD-SCREEN-HOME")
    name: str = Field(..., description="Anchor name")
    artifact_type: GoldenArtifactType
    baseline_reference: str = Field(..., description="Reference snapshot hash or path")
    match_threshold: float = Field(default=0.01, ge=0.0, le=0.05, description="Allowed visual divergence")
    status: ReleaseGateStatus = Field(default=ReleaseGateStatus.PASSED)


class ProductionReleaseReportContract(BaseContractModel):
    """Complete production release verification report (Section 16.56 & 16.60)."""
    release_version: str
    environment: ReleaseEnvironment
    overall_passed: bool
    gates: list[ReleaseGateResultContract]
    checklist_summary: dict[str, int] = Field(..., description="Count of passed vs total items by category")
    golden_screens_count: int = Field(default=15)
    golden_components_count: int = Field(default=15)
    timestamp: str


class VisualTrackStatusContract(BaseContractModel):
    """Master status of the entire VD-0 through VD-16 Visual Design Track (Section 16.61)."""
    phase_statuses: dict[str, str] = Field(..., description="Phase ID to completion percentage (100%)")
    visual_design_architecture_pct: int = Field(default=100)
    visual_specification_pct: int = Field(default=100)
    actual_repository_implementation_pct: int = Field(default=0, description="Handoff state: 0% until repo build begins")
    total_phases: int = Field(default=17)
    status_message: str = Field(..., description="Track completion declaration")
