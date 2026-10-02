/**
 * FashXStudio Interaction, State, Accessibility & Visual QA System Types — Version 1.
 *
 * TypeScript types and interfaces mirroring schemas/visual/interaction.py.
 * Follows Phase 15 (VD-15 Interaction, State, Accessibility & Visual QA System).
 */

export type InteractionState =
  | 'rest'
  | 'hover'
  | 'focus'
  | 'active'
  | 'selected'
  | 'disabled'
  | 'loading'
  | 'success'
  | 'error'
  | 'unavailable';

export type ScreenLifecycleState =
  | 'loading'
  | 'loaded'
  | 'empty'
  | 'error'
  | 'partial'
  | 'offline';

export type FeedbackType =
  | 'toast'
  | 'inline_alert'
  | 'banner'
  | 'dialog'
  | 'status_badge'
  | 'screen_announcement';

export type MotionCategory =
  | 'instant'
  | 'fast'
  | 'normal'
  | 'slow'
  | 'emphasized';

export type VisualRegressionClassification =
  | 'expected'
  | 'intentional'
  | 'content_driven'
  | 'regression'
  | 'unknown';

export interface ComponentStateEvaluationRequest {
  component_id: string;
  is_disabled?: boolean;
  is_loading?: boolean;
  is_error?: boolean;
  is_selected?: boolean;
  is_pressed?: boolean;
  is_focused?: boolean;
  is_hovered?: boolean;
  is_unavailable?: boolean;
  error_message?: string | null;
}

export interface ComponentStateContract {
  component_id: string;
  active_state: InteractionState;
  is_interactive: boolean;
  aria_disabled: boolean;
  aria_busy: boolean;
  aria_selected?: boolean | null;
  aria_invalid: boolean;
  error_message?: string | null;
  focus_ring_visible: boolean;
  touch_target_min_px: number;
}

export interface FormFieldValidationRequest {
  field_id: string;
  field_type?: string;
  value: string;
  is_required?: boolean;
}

export interface FormFieldValidationResult {
  field_id: string;
  is_valid: boolean;
  state: InteractionState;
  error_message?: string | null;
  guidance?: string | null;
  aria_invalid: boolean;
  aria_describedby?: string | null;
}

export interface FeedbackDispatchRequest {
  situation: string;
  title: string;
  message: string;
  action_label?: string | null;
  is_destructive?: boolean;
}

export interface FeedbackEventContract {
  feedback_type: FeedbackType;
  title: string;
  message: string;
  action_label?: string | null;
  auto_dismiss_ms?: number | null;
  dismissible: boolean;
  aria_live: string;
  requires_confirmation: boolean;
}

export interface ScreenStateContract {
  screen_id: string;
  lifecycle_state: ScreenLifecycleState;
  title: string;
  skeleton_layout_type?: string | null;
  empty_heading?: string | null;
  empty_description?: string | null;
  empty_action_label?: string | null;
  error_heading?: string | null;
  error_description?: string | null;
  retry_supported: boolean;
  partial_warning?: string | null;
  is_offline: boolean;
}

export interface AccessibilityAuditRequest {
  target_id: string;
  touch_target_px?: number;
  contrast_ratio?: number;
  has_accessible_name?: boolean;
  has_keyboard_trap?: boolean;
  has_visible_focus?: boolean;
  supports_focus_restoration?: boolean;
  heading_hierarchy_valid?: boolean;
  color_only_indication?: boolean;
  prefers_reduced_motion?: boolean;
}

export interface AccessibilityAuditResult {
  target_id: string;
  is_compliant: boolean;
  violations: string[];
  warnings: string[];
  touch_target_passed: boolean;
  contrast_passed: boolean;
  keyboard_passed: boolean;
  screen_reader_passed: boolean;
  color_independence_passed: boolean;
  reduced_motion_passed: boolean;
}

export interface VisualQASpecContract {
  fixture_id: string;
  component_or_screen_id: string;
  viewport_width_px: number;
  viewport_height_px: number;
  tested_state: InteractionState;
  classification: VisualRegressionClassification;
  pixel_diff_threshold: number;
  is_deterministic: boolean;
}
