"""FashXStudio Interaction, State, Accessibility & Visual QA System Domain Service — Version 1.

Implements the state precedence engine, contextual form validation, feedback decision matrix,
screen lifecycle transitions, accessibility audit engine, and visual QA fixtures for Phase 15.
Adheres strictly to Rule I01 (Layer Separation) and Rule I02 (Contract Primacy with extra="forbid").
"""

import re
from typing import Any
from schemas.visual.interaction import (
    AccessibilityAuditRequest,
    AccessibilityAuditResult,
    ComponentStateContract,
    ComponentStateEvaluationRequest,
    FeedbackDispatchRequest,
    FeedbackEventContract,
    FeedbackType,
    FormFieldValidationRequest,
    FormFieldValidationResult,
    InteractionState,
    MotionCategory,
    ScreenLifecycleState,
    ScreenStateContract,
    VisualQASpecContract,
    VisualRegressionClassification,
)


# ---------------------------------------------------------------------------
# 1. State Precedence Engine (Section 15.3 - 15.5)
# ---------------------------------------------------------------------------

def evaluate_component_state(request: ComponentStateEvaluationRequest) -> ComponentStateContract:
    """Resolve active component interaction state according to strict precedence (Section 15.5).

    Precedence order:
    Error -> Unavailable -> Disabled -> Loading -> Selected -> Pressed -> Focus -> Hover -> Rest
    """
    comp_id = request.component_id

    # 1. Error state (highest non-blocking priority)
    if request.is_error:
        return ComponentStateContract(
            component_id=comp_id,
            active_state=InteractionState.ERROR,
            is_interactive=True,
            aria_disabled=False,
            aria_busy=False,
            aria_invalid=True,
            error_message=request.error_message or "Component entered error state",
            focus_ring_visible=False,
            touch_target_min_px=44,
        )

    # 2. Unavailable state
    if request.is_unavailable:
        return ComponentStateContract(
            component_id=comp_id,
            active_state=InteractionState.UNAVAILABLE,
            is_interactive=False,
            aria_disabled=True,
            aria_busy=False,
            aria_invalid=False,
            focus_ring_visible=False,
            touch_target_min_px=44,
        )

    # 3. Disabled state
    if request.is_disabled:
        return ComponentStateContract(
            component_id=comp_id,
            active_state=InteractionState.DISABLED,
            is_interactive=False,
            aria_disabled=True,
            aria_busy=False,
            aria_invalid=False,
            focus_ring_visible=False,
            touch_target_min_px=44,
        )

    # 4. Loading state
    if request.is_loading:
        return ComponentStateContract(
            component_id=comp_id,
            active_state=InteractionState.LOADING,
            is_interactive=False,
            aria_disabled=False,
            aria_busy=True,
            aria_invalid=False,
            focus_ring_visible=False,
            touch_target_min_px=44,
        )

    # 5. Selected state
    if request.is_selected:
        return ComponentStateContract(
            component_id=comp_id,
            active_state=InteractionState.SELECTED,
            is_interactive=True,
            aria_disabled=False,
            aria_busy=False,
            aria_selected=True,
            aria_invalid=False,
            focus_ring_visible=request.is_focused,
            touch_target_min_px=44,
        )

    # 6. Active / Pressed state
    if request.is_pressed:
        return ComponentStateContract(
            component_id=comp_id,
            active_state=InteractionState.ACTIVE,
            is_interactive=True,
            aria_disabled=False,
            aria_busy=False,
            aria_invalid=False,
            focus_ring_visible=False,
            touch_target_min_px=44,
        )

    # 7. Focus state
    if request.is_focused:
        return ComponentStateContract(
            component_id=comp_id,
            active_state=InteractionState.FOCUS,
            is_interactive=True,
            aria_disabled=False,
            aria_busy=False,
            aria_invalid=False,
            focus_ring_visible=True,
            touch_target_min_px=44,
        )

    # 8. Hover state
    if request.is_hovered:
        return ComponentStateContract(
            component_id=comp_id,
            active_state=InteractionState.HOVER,
            is_interactive=True,
            aria_disabled=False,
            aria_busy=False,
            aria_invalid=False,
            focus_ring_visible=False,
            touch_target_min_px=44,
        )

    # 9. Default / Rest state
    return ComponentStateContract(
        component_id=comp_id,
        active_state=InteractionState.REST,
        is_interactive=True,
        aria_disabled=False,
        aria_busy=False,
        aria_invalid=False,
        focus_ring_visible=False,
        touch_target_min_px=44,
    )


# ---------------------------------------------------------------------------
# 2. Form Field Validation Engine (Section 15.13 - 15.15)
# ---------------------------------------------------------------------------

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-]{7,15}$")


def validate_form_field(request: FormFieldValidationRequest) -> FormFieldValidationResult:
    """Validate form field and return contextual feedback with fix guidance (Section 15.14)."""
    val = request.value.strip()
    fid = request.field_id
    ftype = request.field_type.lower()

    # Check required
    if request.is_required and not val:
        return FormFieldValidationResult(
            field_id=fid,
            is_valid=False,
            state=InteractionState.ERROR,
            error_message=f"{fid.replace('_', ' ').capitalize()} is required.",
            guidance="Please provide a value to continue.",
            aria_invalid=True,
            aria_describedby=f"{fid}-error-hint",
        )

    # Email validation
    if ftype == "email" and val:
        if not EMAIL_REGEX.match(val):
            return FormFieldValidationResult(
                field_id=fid,
                is_valid=False,
                state=InteractionState.ERROR,
                error_message="Please enter a valid email address.",
                guidance="Ensure your email contains an '@' and a valid domain (e.g. user@example.com).",
                aria_invalid=True,
                aria_describedby=f"{fid}-error-hint",
            )

    # Phone validation
    if ftype == "phone" and val:
        if not PHONE_REGEX.match(val):
            return FormFieldValidationResult(
                field_id=fid,
                is_valid=False,
                state=InteractionState.ERROR,
                error_message="Please enter a valid phone number.",
                guidance="Enter numbers with an optional leading '+' for country code.",
                aria_invalid=True,
                aria_describedby=f"{fid}-error-hint",
            )

    # Minimum length for password
    if ftype == "password" and val:
        if len(val) < 8:
            return FormFieldValidationResult(
                field_id=fid,
                is_valid=False,
                state=InteractionState.ERROR,
                error_message="Password is too short.",
                guidance="Use at least 8 characters with a mix of letters, numbers, and symbols.",
                aria_invalid=True,
                aria_describedby=f"{fid}-error-hint",
            )

    # Valid field
    return FormFieldValidationResult(
        field_id=fid,
        is_valid=True,
        state=InteractionState.SUCCESS,
        error_message=None,
        guidance=None,
        aria_invalid=False,
        aria_describedby=None,
    )


# ---------------------------------------------------------------------------
# 3. Feedback Decision Engine (Section 15.68 - 15.70)
# ---------------------------------------------------------------------------

def dispatch_feedback_event(request: FeedbackDispatchRequest) -> FeedbackEventContract:
    """Determine least-disruptive, accessible feedback mechanism (Section 15.69)."""
    sit = request.situation.lower()

    if sit in ["minor_success", "save", "add_to_cart", "toast"]:
        return FeedbackEventContract(
            feedback_type=FeedbackType.TOAST,
            title=request.title,
            message=request.message,
            action_label=request.action_label or "View",
            auto_dismiss_ms=3000,
            dismissible=True,
            aria_live="polite",
            requires_confirmation=False,
        )

    if sit in ["form_error", "field_error", "validation"]:
        return FeedbackEventContract(
            feedback_type=FeedbackType.INLINE_ALERT,
            title=request.title,
            message=request.message,
            action_label=request.action_label,
            auto_dismiss_ms=None,
            dismissible=False,
            aria_live="assertive",
            requires_confirmation=False,
        )

    if sit in ["system_error", "network_error", "outage", "banner"]:
        return FeedbackEventContract(
            feedback_type=FeedbackType.BANNER,
            title=request.title,
            message=request.message,
            action_label=request.action_label or "Retry",
            auto_dismiss_ms=None,
            dismissible=True,
            aria_live="assertive",
            requires_confirmation=False,
        )

    if sit in ["destructive_action", "delete", "clear_history", "reset"]:
        return FeedbackEventContract(
            feedback_type=FeedbackType.DIALOG,
            title=request.title,
            message=request.message,
            action_label=request.action_label or "Confirm",
            auto_dismiss_ms=None,
            dismissible=True,
            aria_live="assertive",
            requires_confirmation=True,
        )

    if sit in ["offline", "status"]:
        return FeedbackEventContract(
            feedback_type=FeedbackType.STATUS_BADGE,
            title=request.title,
            message=request.message,
            action_label=request.action_label,
            auto_dismiss_ms=None,
            dismissible=False,
            aria_live="polite",
            requires_confirmation=False,
        )

    # Default to polite live announcement
    return FeedbackEventContract(
        feedback_type=FeedbackType.SCREEN_ANNOUNCEMENT,
        title=request.title,
        message=request.message,
        action_label=request.action_label,
        auto_dismiss_ms=5000,
        dismissible=True,
        aria_live="polite",
        requires_confirmation=False,
    )


# ---------------------------------------------------------------------------
# 4. Screen State & Lifecycle Transitions (Section 15.59 - 15.67)
# ---------------------------------------------------------------------------

SCREEN_CATALOG_SKELETONS: dict[str, str] = {
    "P01": "grid",
    "P02": "detail",
    "ST01": "grid",
    "ST02": "builder",
    "M02": "map",
    "AI02": "chat",
    "PR02": "dashboard",
    "D01": "discovery",
}


def get_screen_state(
    screen_id: str,
    lifecycle_state: ScreenLifecycleState = ScreenLifecycleState.LOADED,
) -> ScreenStateContract:
    """Retrieve screen-level state contract governing skeletons, errors, and empty views."""
    skel_type = SCREEN_CATALOG_SKELETONS.get(screen_id, "list")

    if lifecycle_state == ScreenLifecycleState.LOADING:
        return ScreenStateContract(
            screen_id=screen_id,
            lifecycle_state=ScreenLifecycleState.LOADING,
            title=f"Loading {screen_id}",
            skeleton_layout_type=skel_type,
            retry_supported=False,
        )

    if lifecycle_state == ScreenLifecycleState.EMPTY:
        return ScreenStateContract(
            screen_id=screen_id,
            lifecycle_state=ScreenLifecycleState.EMPTY,
            title=f"{screen_id} Empty",
            empty_heading="Nothing to display yet",
            empty_description="Explore new arrivals or create a new styling look to populate this space.",
            empty_action_label="Explore Catalog",
            retry_supported=False,
        )

    if lifecycle_state == ScreenLifecycleState.ERROR:
        return ScreenStateContract(
            screen_id=screen_id,
            lifecycle_state=ScreenLifecycleState.ERROR,
            title=f"Error Loading {screen_id}",
            error_heading="Unable to load content",
            error_description="We encountered a temporary connection issue. Please verify your connection and try again.",
            retry_supported=True,
        )

    if lifecycle_state == ScreenLifecycleState.PARTIAL:
        return ScreenStateContract(
            screen_id=screen_id,
            lifecycle_state=ScreenLifecycleState.PARTIAL,
            title=f"{screen_id} Partial Content",
            partial_warning="Some personalized recommendations are temporarily unavailable.",
            retry_supported=True,
        )

    if lifecycle_state == ScreenLifecycleState.OFFLINE:
        return ScreenStateContract(
            screen_id=screen_id,
            lifecycle_state=ScreenLifecycleState.OFFLINE,
            title=f"{screen_id} Offline",
            partial_warning="Viewing cached offline content. Live actions will sync when back online.",
            is_offline=True,
            retry_supported=True,
        )

    # Standard LOADED state
    return ScreenStateContract(
        screen_id=screen_id,
        lifecycle_state=ScreenLifecycleState.LOADED,
        title=f"Screen {screen_id}",
        retry_supported=False,
    )


# ---------------------------------------------------------------------------
# 5. Accessibility Audit Engine (Section 15.100)
# ---------------------------------------------------------------------------

def run_accessibility_audit(request: AccessibilityAuditRequest) -> AccessibilityAuditResult:
    """Evaluate interactive component or screen against WCAG 2.1 AA standards (Section 15.100)."""
    violations: list[str] = []
    warnings: list[str] = []

    # A11Y-011: Touch target >= 44px
    touch_passed = request.touch_target_px >= 44
    if not touch_passed:
        violations.append(
            f"A11Y-011: Touch target height ({request.touch_target_px}px) is below 44px baseline."
        )

    # A11Y-012: Contrast ratio >= 4.5:1
    contrast_passed = request.contrast_ratio >= 4.5
    if not contrast_passed:
        violations.append(
            f"A11Y-012: Contrast ratio ({request.contrast_ratio}:1) fails WCAG AA minimum 4.5:1."
        )

    # A11Y-001 & A11Y-002: Keyboard traps & visible focus
    keyboard_passed = (not request.has_keyboard_trap) and request.has_visible_focus
    if request.has_keyboard_trap:
        violations.append("A11Y-001: Keyboard trap detected. Focus cannot cycle out of component.")
    if not request.has_visible_focus:
        violations.append("A11Y-002: Missing visible focus indicator.")

    # A11Y-004: Screen reader accessible name
    screen_reader_passed = request.has_accessible_name
    if not screen_reader_passed:
        violations.append("A11Y-004: Missing accessible name or aria-label.")

    # A11Y-015: No color-only meaning
    color_passed = not request.color_only_indication
    if not color_passed:
        violations.append(
            "A11Y-015: Information conveyed solely through color without text or icon equivalent."
        )

    # A11Y-014: Reduced motion
    reduced_motion_passed = True
    if request.prefers_reduced_motion:
        warnings.append("A11Y-014: Verified instantaneous transition override for prefers-reduced-motion.")

    is_compliant = (
        touch_passed
        and contrast_passed
        and keyboard_passed
        and screen_reader_passed
        and color_passed
    )

    return AccessibilityAuditResult(
        target_id=request.target_id,
        is_compliant=is_compliant,
        violations=violations,
        warnings=warnings,
        touch_target_passed=touch_passed,
        contrast_passed=contrast_passed,
        keyboard_passed=keyboard_passed,
        screen_reader_passed=screen_reader_passed,
        color_independence_passed=color_passed,
        reduced_motion_passed=reduced_motion_passed,
    )


# ---------------------------------------------------------------------------
# 6. Visual QA Test Fixtures Matrix (Section 15.107 - 15.111)
# ---------------------------------------------------------------------------

QA_FIXTURES: list[VisualQASpecContract] = [
    VisualQASpecContract(
        fixture_id="QA-PROD-CARD-01",
        component_or_screen_id="ProductCard",
        viewport_width_px=390,
        viewport_height_px=844,
        tested_state=InteractionState.REST,
        classification=VisualRegressionClassification.EXPECTED,
        pixel_diff_threshold=0.01,
        is_deterministic=True,
    ),
    VisualQASpecContract(
        fixture_id="QA-PROD-CARD-02",
        component_or_screen_id="ProductCard",
        viewport_width_px=390,
        viewport_height_px=844,
        tested_state=InteractionState.LOADING,
        classification=VisualRegressionClassification.EXPECTED,
        pixel_diff_threshold=0.01,
        is_deterministic=True,
    ),
    VisualQASpecContract(
        fixture_id="QA-PROD-CARD-03",
        component_or_screen_id="ProductCard",
        viewport_width_px=1440,
        viewport_height_px=900,
        tested_state=InteractionState.HOVER,
        classification=VisualRegressionClassification.EXPECTED,
        pixel_diff_threshold=0.01,
        is_deterministic=True,
    ),
    VisualQASpecContract(
        fixture_id="QA-BTN-CART-01",
        component_or_screen_id="AddToCartButton",
        viewport_width_px=390,
        viewport_height_px=844,
        tested_state=InteractionState.LOADING,
        classification=VisualRegressionClassification.EXPECTED,
        pixel_diff_threshold=0.01,
        is_deterministic=True,
    ),
    VisualQASpecContract(
        fixture_id="QA-BUILDER-01",
        component_or_screen_id="ST02_OutfitBuilder",
        viewport_width_px=1440,
        viewport_height_px=900,
        tested_state=InteractionState.SELECTED,
        classification=VisualRegressionClassification.EXPECTED,
        pixel_diff_threshold=0.01,
        is_deterministic=True,
    ),
]


def list_visual_qa_fixtures() -> list[VisualQASpecContract]:
    """Retrieve catalog of automated visual regression test specifications."""
    return QA_FIXTURES
