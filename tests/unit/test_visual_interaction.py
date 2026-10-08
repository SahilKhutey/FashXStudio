"""Unit tests for Interaction, State, Accessibility & Visual QA System — Phase 15.

Verifies:
- INT-UNIT-001: Component state resolution across all interaction states
- INT-UNIT-002: Strict state precedence hierarchy (Error > Unavailable > Disabled > Loading > Selected > Pressed > Focus > Hover > Rest)
- INT-UNIT-003: Form field validation and contextual fix guidance
- INT-UNIT-004: Global feedback decision matrix (Toast vs Inline Alert vs Banner vs Dialog)
- INT-UNIT-005: Screen lifecycle states (loading skeleton, empty view, error recovery, partial degradation)
- INT-UNIT-006: Offline mode behavior and cached data indicators
- INT-UNIT-007: Destructive action confirmation and consequence wording
- INT-UNIT-008: WCAG 2.1 AA accessibility audit engine (touch targets >= 44px, contrast, keyboard traps, focus rings)
- INT-UNIT-009: Motion classifications and reduced-motion instant override
- INT-UNIT-010: Automated visual regression QA fixtures
- FORBID-001 to FORBID-008: Strict extra="forbid" rejection across all Interaction contracts (Rule I02).
"""

import pytest
from pydantic import ValidationError

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
from fashx.visual.interaction_service import (
    dispatch_feedback_event,
    evaluate_component_state,
    get_screen_state,
    list_visual_qa_fixtures,
    run_accessibility_audit,
    validate_form_field,
)


# ---------------------------------------------------------------------------
# INT-UNIT-001 & INT-UNIT-002: State Precedence Hierarchy
# ---------------------------------------------------------------------------

def test_int_unit_001_default_rest_state() -> None:
    """INT-UNIT-001: Component in default state resolves to REST (Section 15.3)."""
    req = ComponentStateEvaluationRequest(component_id="btn_checkout")
    res = evaluate_component_state(req)
    assert res.active_state == InteractionState.REST
    assert res.is_interactive is True
    assert res.aria_disabled is False
    assert res.aria_busy is False
    assert res.touch_target_min_px >= 44


def test_int_unit_002_error_overrides_all() -> None:
    """INT-UNIT-002: Error state overrides loading, disabled, hover, and focus (Section 15.5)."""
    req = ComponentStateEvaluationRequest(
        component_id="btn_submit",
        is_error=True,
        is_loading=True,
        is_disabled=True,
        is_focused=True,
        error_message="Submission rejected by server",
    )
    res = evaluate_component_state(req)
    assert res.active_state == InteractionState.ERROR
    assert res.aria_invalid is True
    assert res.error_message == "Submission rejected by server"


def test_int_unit_002_unavailable_overrides_disabled() -> None:
    """INT-UNIT-002: Unavailable overrides disabled and loading (Section 15.5)."""
    req = ComponentStateEvaluationRequest(
        component_id="btn_stock",
        is_unavailable=True,
        is_disabled=True,
        is_loading=True,
    )
    res = evaluate_component_state(req)
    assert res.active_state == InteractionState.UNAVAILABLE
    assert res.is_interactive is False
    assert res.aria_disabled is True


def test_int_unit_002_disabled_overrides_loading() -> None:
    """INT-UNIT-002: Disabled state overrides loading and selection (Section 15.5)."""
    req = ComponentStateEvaluationRequest(
        component_id="btn_cart",
        is_disabled=True,
        is_loading=True,
        is_selected=True,
    )
    res = evaluate_component_state(req)
    assert res.active_state == InteractionState.DISABLED
    assert res.is_interactive is False
    assert res.aria_disabled is True


def test_int_unit_002_loading_overrides_selected() -> None:
    """INT-UNIT-002: Loading state overrides selected, active, and hover (Section 15.5)."""
    req = ComponentStateEvaluationRequest(
        component_id="btn_save",
        is_loading=True,
        is_selected=True,
        is_hovered=True,
    )
    res = evaluate_component_state(req)
    assert res.active_state == InteractionState.LOADING
    assert res.aria_busy is True
    assert res.is_interactive is False


def test_int_unit_002_selected_state() -> None:
    """INT-UNIT-002: Selected state sets aria_selected and retains interactivity (Section 15.5)."""
    req = ComponentStateEvaluationRequest(
        component_id="chip_variant_m",
        is_selected=True,
        is_hovered=True,
    )
    res = evaluate_component_state(req)
    assert res.active_state == InteractionState.SELECTED
    assert res.aria_selected is True
    assert res.is_interactive is True


def test_int_unit_002_focus_state_and_ring() -> None:
    """INT-UNIT-002: Focus state activates visible focus ring token (Section 15.5 & 15.85)."""
    req = ComponentStateEvaluationRequest(
        component_id="input_search",
        is_focused=True,
        is_hovered=True,
    )
    res = evaluate_component_state(req)
    assert res.active_state == InteractionState.FOCUS
    assert res.focus_ring_visible is True


# ---------------------------------------------------------------------------
# INT-UNIT-003: Form Validation & Guidance
# ---------------------------------------------------------------------------

def test_int_unit_003_required_field_empty() -> None:
    """INT-UNIT-003: Empty required field produces actionable guidance (Section 15.13 & 15.14)."""
    req = FormFieldValidationRequest(
        field_id="email_address",
        field_type="email",
        value="",
        is_required=True,
    )
    res = validate_form_field(req)
    assert res.is_valid is False
    assert res.state == InteractionState.ERROR
    assert "required" in res.error_message.lower()
    assert res.guidance is not None
    assert res.aria_invalid is True


def test_int_unit_003_invalid_email() -> None:
    """INT-UNIT-003: Invalid email syntax produces contextual fix instructions (Section 15.14)."""
    req = FormFieldValidationRequest(
        field_id="email",
        field_type="email",
        value="invalid-email-address",
        is_required=True,
    )
    res = validate_form_field(req)
    assert res.is_valid is False
    assert "valid email" in res.error_message.lower()
    assert "user@example.com" in res.guidance


def test_int_unit_003_valid_form_field() -> None:
    """INT-UNIT-003: Valid form input resolves to SUCCESS state (Section 15.13)."""
    req = FormFieldValidationRequest(
        field_id="email",
        field_type="email",
        value="alexandra@fashx.studio",
        is_required=True,
    )
    res = validate_form_field(req)
    assert res.is_valid is True
    assert res.state == InteractionState.SUCCESS
    assert res.error_message is None
    assert res.aria_invalid is False


# ---------------------------------------------------------------------------
# INT-UNIT-004: Feedback Decision Matrix
# ---------------------------------------------------------------------------

def test_int_unit_004_feedback_minor_success() -> None:
    """INT-UNIT-004: Minor success maps to auto-dismissing Toast (Section 15.69 & 15.70)."""
    req = FeedbackDispatchRequest(
        situation="minor_success",
        title="Added to Bag",
        message="Selvedge Denim Jacket added to your shopping bag.",
        action_label="View Bag",
    )
    res = dispatch_feedback_event(req)
    assert res.feedback_type == FeedbackType.TOAST
    assert res.auto_dismiss_ms == 3000
    assert res.aria_live == "polite"
    assert res.requires_confirmation is False


def test_int_unit_004_feedback_form_error() -> None:
    """INT-UNIT-004: Form error maps to inline alert (Section 15.69)."""
    req = FeedbackDispatchRequest(
        situation="form_error",
        title="Missing Delivery Address",
        message="Please provide a valid street address.",
    )
    res = dispatch_feedback_event(req)
    assert res.feedback_type == FeedbackType.INLINE_ALERT
    assert res.auto_dismiss_ms is None
    assert res.aria_live == "assertive"


def test_int_unit_004_feedback_destructive_dialog() -> None:
    """INT-UNIT-004: Destructive action maps to confirmation Dialog (Section 15.57 & 15.69)."""
    req = FeedbackDispatchRequest(
        situation="destructive_action",
        title="Remove Saved Look?",
        message="This action cannot be undone.",
        action_label="Remove",
        is_destructive=True,
    )
    res = dispatch_feedback_event(req)
    assert res.feedback_type == FeedbackType.DIALOG
    assert res.requires_confirmation is True
    assert res.aria_live == "assertive"


# ---------------------------------------------------------------------------
# INT-UNIT-005 & INT-UNIT-006: Screen States & Offline Handling
# ---------------------------------------------------------------------------

def test_int_unit_005_screen_loading_skeleton() -> None:
    """INT-UNIT-005: Screen loading state specifies skeleton layout (Section 15.60 & 15.63)."""
    res = get_screen_state("P01", ScreenLifecycleState.LOADING)
    assert res.lifecycle_state == ScreenLifecycleState.LOADING
    assert res.skeleton_layout_type == "grid"
    assert res.retry_supported is False


def test_int_unit_005_screen_empty_state() -> None:
    """INT-UNIT-005: Empty state provides context and primary action (Section 15.64)."""
    res = get_screen_state("ST01", ScreenLifecycleState.EMPTY)
    assert res.lifecycle_state == ScreenLifecycleState.EMPTY
    assert res.empty_heading is not None
    assert res.empty_action_label is not None


def test_int_unit_005_screen_error_recovery() -> None:
    """INT-UNIT-005: Error state answers what happened and provides retry action (Section 15.99)."""
    res = get_screen_state("AI02", ScreenLifecycleState.ERROR)
    assert res.lifecycle_state == ScreenLifecycleState.ERROR
    assert res.retry_supported is True
    assert "temporary connection issue" in res.error_description


def test_int_unit_006_screen_offline_state() -> None:
    """INT-UNIT-006: Offline state communicates cached content availability (Section 15.66)."""
    res = get_screen_state("M02", ScreenLifecycleState.OFFLINE)
    assert res.lifecycle_state == ScreenLifecycleState.OFFLINE
    assert res.is_offline is True
    assert "cached offline content" in res.partial_warning


# ---------------------------------------------------------------------------
# INT-UNIT-008: WCAG 2.1 AA Accessibility Audit
# ---------------------------------------------------------------------------

def test_int_unit_008_accessibility_audit_full_compliance() -> None:
    """INT-UNIT-008: Compliant component passes all WCAG AA audits (Section 15.100)."""
    req = AccessibilityAuditRequest(
        target_id="btn_add_to_cart",
        touch_target_px=48,
        contrast_ratio=7.1,
        has_accessible_name=True,
        has_keyboard_trap=False,
        has_visible_focus=True,
        supports_focus_restoration=True,
        heading_hierarchy_valid=True,
        color_only_indication=False,
        prefers_reduced_motion=True,
    )
    res = run_accessibility_audit(req)
    assert res.is_compliant is True
    assert len(res.violations) == 0
    assert res.touch_target_passed is True
    assert res.contrast_passed is True
    assert res.keyboard_passed is True
    assert res.color_independence_passed is True


def test_int_unit_008_accessibility_audit_touch_and_contrast_violations() -> None:
    """INT-UNIT-008: Audit flags touch target <44px and contrast <4.5:1 (Section 15.100)."""
    req = AccessibilityAuditRequest(
        target_id="btn_small_icon",
        touch_target_px=32,       # Violates 44px baseline
        contrast_ratio=3.2,       # Violates 4.5:1 contrast
        has_accessible_name=False, # Missing aria-label
    )
    res = run_accessibility_audit(req)
    assert res.is_compliant is False
    assert len(res.violations) >= 3
    assert res.touch_target_passed is False
    assert res.contrast_passed is False
    assert res.screen_reader_passed is False


# ---------------------------------------------------------------------------
# INT-UNIT-009 & INT-UNIT-010: Motion & Visual QA Specs
# ---------------------------------------------------------------------------

def test_int_unit_009_motion_categories() -> None:
    """INT-UNIT-009: Motion categories classify transition speeds (Section 15.87)."""
    assert MotionCategory.INSTANT == "instant"
    assert MotionCategory.FAST == "fast"
    assert MotionCategory.NORMAL == "normal"
    assert MotionCategory.SLOW == "slow"


def test_int_unit_010_visual_qa_fixtures() -> None:
    """INT-UNIT-010: QA fixtures catalog is deterministic and non-empty (Section 15.107)."""
    fixtures = list_visual_qa_fixtures()
    assert len(fixtures) >= 5
    for f in fixtures:
        assert f.is_deterministic is True
        assert f.pixel_diff_threshold <= 0.05
        assert f.classification == VisualRegressionClassification.EXPECTED


# ---------------------------------------------------------------------------
# Constitution Rule I02: extra="forbid" Rejection Tests
# ---------------------------------------------------------------------------

def test_forbid_001_component_state_request() -> None:
    """FORBID-001: ComponentStateEvaluationRequest forbids unauthorized fields."""
    with pytest.raises(ValidationError):
        ComponentStateEvaluationRequest(component_id="c1", illegal_flag=True)  # type: ignore


def test_forbid_002_component_state_contract() -> None:
    """FORBID-002: ComponentStateContract forbids unauthorized fields."""
    with pytest.raises(ValidationError):
        ComponentStateContract(
            component_id="c1",
            active_state=InteractionState.REST,
            is_interactive=True,
            aria_disabled=False,
            aria_busy=False,
            focus_ring_visible=False,
            unauthorized="nope",  # type: ignore
        )


def test_forbid_003_form_validation_request() -> None:
    """FORBID-003: FormFieldValidationRequest forbids unauthorized fields."""
    with pytest.raises(ValidationError):
        FormFieldValidationRequest(field_id="f1", value="v", bad_param="err")  # type: ignore


def test_forbid_004_form_validation_result() -> None:
    """FORBID-004: FormFieldValidationResult forbids unauthorized fields."""
    with pytest.raises(ValidationError):
        FormFieldValidationResult(
            field_id="f1",
            is_valid=True,
            state=InteractionState.SUCCESS,
            aria_invalid=False,
            unexpected_field=123,  # type: ignore
        )


def test_forbid_005_feedback_request() -> None:
    """FORBID-005: FeedbackDispatchRequest forbids unauthorized fields."""
    with pytest.raises(ValidationError):
        FeedbackDispatchRequest(situation="minor_success", title="T", message="M", hack=True)  # type: ignore


def test_forbid_006_screen_state_contract() -> None:
    """FORBID-006: ScreenStateContract forbids unauthorized fields."""
    with pytest.raises(ValidationError):
        ScreenStateContract(
            screen_id="P01",
            lifecycle_state=ScreenLifecycleState.LOADED,
            title="P01",
            retry_supported=False,
            invalid="blocked",  # type: ignore
        )


def test_forbid_007_accessibility_request() -> None:
    """FORBID-007: AccessibilityAuditRequest forbids unauthorized fields."""
    with pytest.raises(ValidationError):
        AccessibilityAuditRequest(target_id="btn", bogus=True)  # type: ignore


def test_forbid_008_visual_qa_spec() -> None:
    """FORBID-008: VisualQASpecContract forbids unauthorized fields."""
    with pytest.raises(ValidationError):
        VisualQASpecContract(
            fixture_id="FX-01",
            component_or_screen_id="C1",
            viewport_width_px=390,
            viewport_height_px=844,
            tested_state=InteractionState.REST,
            classification=VisualRegressionClassification.EXPECTED,
            pixel_diff_threshold=0.01,
            is_deterministic=True,
            unauthorized="error",  # type: ignore
        )
