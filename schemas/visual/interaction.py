"""FashXStudio Interaction, State, Accessibility & Visual QA System Contracts — Version 1.

Defines the state hierarchy, component states, feedback decision matrix, screen lifecycles,
accessibility audits, and visual QA verification contracts for Phase 15 (VD-15).
Adheres strictly to Constitution Rule I02 (Contract Primacy) with extra="forbid".
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class InteractionState(StrEnum):
    """Component interaction state hierarchy (Section 15.3 & 15.4)."""
    REST = "rest"
    HOVER = "hover"
    FOCUS = "focus"
    ACTIVE = "active"          # Pressed
    SELECTED = "selected"
    DISABLED = "disabled"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class ScreenLifecycleState(StrEnum):
    """Screen-level data and operational state (Section 15.59 - 15.67)."""
    LOADING = "loading"
    LOADED = "loaded"
    EMPTY = "empty"
    ERROR = "error"
    PARTIAL = "partial"
    OFFLINE = "offline"


class FeedbackType(StrEnum):
    """Global feedback mechanisms based on disruption hierarchy (Section 15.68 & 15.69)."""
    TOAST = "toast"                        # Minor successful action (short, dismissible)
    INLINE_ALERT = "inline_alert"          # Form field or section validation error
    BANNER = "banner"                      # Major system issue, partial outage
    DIALOG = "dialog"                      # High-impact destructive confirmation
    STATUS_BADGE = "status_badge"          # Persistent item status
    SCREEN_ANNOUNCEMENT = "screen_announcement"  # Assistive technology live region


class MotionCategory(StrEnum):
    """Motion classification system (Section 15.87 & 15.88)."""
    INSTANT = "instant"      # 0ms (reduced-motion override)
    FAST = "fast"            # 100-150ms (microinteractions, toggles)
    NORMAL = "normal"        # 200-300ms (drawers, sheets, modals)
    SLOW = "slow"            # 400-500ms (large layout reordering)
    EMPHASIZED = "emphasized"  # Complex bezier choreographies


class VisualRegressionClassification(StrEnum):
    """Visual difference triage classification (Section 15.108)."""
    EXPECTED = "expected"              # Intentional design token or layout update
    INTENTIONAL = "intentional"        # Explicit feature enhancement
    CONTENT_DRIVEN = "content_driven"  # Dynamic catalog or copy change
    REGRESSION = "regression"          # Visual defect requiring fix
    UNKNOWN = "unknown"                # Unclassified delta requiring review


# ---------------------------------------------------------------------------
# Component State Contracts
# ---------------------------------------------------------------------------

class ComponentStateEvaluationRequest(BaseContractModel):
    """Input payload to evaluate the active component state under multiple conditions (Section 15.5)."""
    component_id: str = Field(..., description="Unique component or control ID")
    is_disabled: bool = Field(default=False)
    is_loading: bool = Field(default=False)
    is_error: bool = Field(default=False)
    is_selected: bool = Field(default=False)
    is_pressed: bool = Field(default=False)
    is_focused: bool = Field(default=False)
    is_hovered: bool = Field(default=False)
    is_unavailable: bool = Field(default=False)
    error_message: str | None = Field(default=None)


class ComponentStateContract(BaseContractModel):
    """Resolved component interaction state with accessibility metadata (Section 15.4 & 15.5)."""
    component_id: str
    active_state: InteractionState
    is_interactive: bool
    aria_disabled: bool
    aria_busy: bool
    aria_selected: bool | None = None
    aria_invalid: bool = False
    error_message: str | None = None
    focus_ring_visible: bool
    touch_target_min_px: int = Field(default=44, ge=44)


# ---------------------------------------------------------------------------
# Form Validation Contracts
# ---------------------------------------------------------------------------

class FormFieldValidationRequest(BaseContractModel):
    """Input to validate a form field and generate contextual guidance (Section 15.13 & 15.14)."""
    field_id: str = Field(..., description="Field identifier e.g. email, phone, size")
    field_type: str = Field(default="text", description="text, email, password, postal_code, etc.")
    value: str = Field(..., description="Current user input value")
    is_required: bool = Field(default=True)


class FormFieldValidationResult(BaseContractModel):
    """Contextual form validation feedback with actionable fix instructions (Section 15.14)."""
    field_id: str
    is_valid: bool
    state: InteractionState
    error_message: str | None = None
    guidance: str | None = None
    aria_invalid: bool
    aria_describedby: str | None = None


# ---------------------------------------------------------------------------
# Feedback & Notifications
# ---------------------------------------------------------------------------

class FeedbackDispatchRequest(BaseContractModel):
    """Request to generate appropriate user feedback based on situation (Section 15.69)."""
    situation: str = Field(..., description="minor_success, form_error, system_error, destructive_action, offline")
    title: str = Field(..., description="Feedback headline")
    message: str = Field(..., description="Descriptive feedback body")
    action_label: str | None = Field(default=None, description="Optional action label e.g. Undo, Retry")
    is_destructive: bool = Field(default=False)


class FeedbackEventContract(BaseContractModel):
    """Resolved feedback event with delivery mechanism and a11y live level (Section 15.68 - 15.70)."""
    feedback_type: FeedbackType
    title: str
    message: str
    action_label: str | None = None
    auto_dismiss_ms: int | None = None
    dismissible: bool = True
    aria_live: str = Field(default="polite", description="polite, assertive, or off")
    requires_confirmation: bool = False


# ---------------------------------------------------------------------------
# Screen State & Lifecycle
# ---------------------------------------------------------------------------

class ScreenStateContract(BaseContractModel):
    """Screen-level state contract governing skeletons, errors, and empty views (Section 15.59 - 15.67)."""
    screen_id: str
    lifecycle_state: ScreenLifecycleState
    title: str
    skeleton_layout_type: str | None = Field(default=None, description="grid, detail, list, editorial")
    empty_heading: str | None = None
    empty_description: str | None = None
    empty_action_label: str | None = None
    error_heading: str | None = None
    error_description: str | None = None
    retry_supported: bool = True
    partial_warning: str | None = None
    is_offline: bool = False


# ---------------------------------------------------------------------------
# Accessibility & Visual QA Contracts
# ---------------------------------------------------------------------------

class AccessibilityAuditRequest(BaseContractModel):
    """Request to audit interactive component or screen against WCAG 2.1 AA (Section 15.100)."""
    target_id: str = Field(..., description="Screen ID or Component ID to audit")
    touch_target_px: int = Field(default=44, ge=0)
    contrast_ratio: float = Field(default=4.5, ge=0.0)
    has_accessible_name: bool = Field(default=True)
    has_keyboard_trap: bool = Field(default=False)
    has_visible_focus: bool = Field(default=True)
    supports_focus_restoration: bool = Field(default=True)
    heading_hierarchy_valid: bool = Field(default=True)
    color_only_indication: bool = Field(default=False, description="Communicating state solely through color")
    prefers_reduced_motion: bool = Field(default=False)


class AccessibilityAuditResult(BaseContractModel):
    """Audit evaluation result across the 15 WCAG standards (Section 15.100)."""
    target_id: str
    is_compliant: bool
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    touch_target_passed: bool
    contrast_passed: bool
    keyboard_passed: bool
    screen_reader_passed: bool
    color_independence_passed: bool
    reduced_motion_passed: bool


class VisualQASpecContract(BaseContractModel):
    """Fixture specification for automated visual regression tests (Section 15.107 - 15.111)."""
    fixture_id: str = Field(..., description="Unique test fixture ID e.g. QA-PROD-CARD-01")
    component_or_screen_id: str
    viewport_width_px: int
    viewport_height_px: int
    tested_state: InteractionState
    classification: VisualRegressionClassification = Field(default=VisualRegressionClassification.EXPECTED)
    pixel_diff_threshold: float = Field(default=0.01, ge=0.0, le=1.0)
    is_deterministic: bool = Field(default=True)
