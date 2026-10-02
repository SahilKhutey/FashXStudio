/**
 * FashXStudio Responsive & Adaptive Visual System Types — Version 1.
 *
 * TypeScript types and interfaces mirroring schemas/visual/responsive.py.
 * Follows Phase 14 (VD-14 Responsive / Adaptive Visual System).
 */

export type ResponsiveBreakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

export type LayoutMode = 'compact' | 'adaptive' | 'expanded';

export type InteractionInputMode = 'touch' | 'mouse' | 'keyboard' | 'pointer';

export type DeviceOrientation = 'portrait' | 'landscape';

export type ContentPriorityLevel =
  | 'p0_required'
  | 'p1_important'
  | 'p2_supporting'
  | 'p3_optional';

export type NavigationAdaptationType =
  | 'desktop_sidebar'
  | 'tablet_compact_sidebar'
  | 'mobile_bottom_nav_drawer';

export type ModalAdaptationType =
  | 'centered_modal'
  | 'right_drawer'
  | 'bottom_sheet'
  | 'full_screen';

export type FilterAdaptationType =
  | 'sidebar_filters'
  | 'filter_button_drawer'
  | 'bottom_sheet_filter';

export type OutfitBuilderLayoutType =
  | 'desktop_3_column'
  | 'tablet_2_column'
  | 'mobile_canvas_sheet';

export type MapLayoutType =
  | 'desktop_side_results'
  | 'mobile_map_bottom_sheet';

export type CheckoutLayoutType =
  | 'desktop_2_column'
  | 'mobile_accordion_sticky';

export interface SafeAreaInsetsContract {
  top_px: number;
  bottom_px: number;
  left_px: number;
  right_px: number;
}

export interface ResponsiveContainerContract {
  breakpoint: ResponsiveBreakpoint;
  min_width_px: number;
  max_width_px?: number | null;
  container_max_width_px: number;
  horizontal_padding_px: number;
  gutter_px: number;
  default_columns: number;
}

export interface ResponsiveGridCalculationRequest {
  available_width_px: number;
  card_min_width_px?: number;
  gap_px?: number;
  max_columns?: number;
}

export interface ResponsiveGridCalculationResult {
  available_width_px: number;
  computed_columns: number;
  card_width_px: number;
  gap_px: number;
  utilization_pct: number;
}

export interface CardContentPruningRequest {
  layout_mode: LayoutMode;
  image_url: string;
  title: string;
  primary_action_label: string;
  brand?: string | null;
  price_formatted?: string | null;
  availability?: string | null;
  secondary_specs?: Record<string, string>;
  tags?: string[];
}

export interface CardContentPruningResult {
  layout_mode: LayoutMode;
  rendered_fields: string[];
  pruned_fields: string[];
  touch_target_min_px: number;
  display_brand: boolean;
  display_price: boolean;
  display_availability: boolean;
  display_secondary_specs: boolean;
  display_tags: boolean;
}

export interface ViewportEvaluationRequest {
  width_px: number;
  height_px: number;
  input_mode?: InteractionInputMode;
  prefers_reduced_motion?: boolean;
  text_zoom_factor?: number;
  safe_area_insets?: SafeAreaInsetsContract;
}

export interface ViewportEvaluationResult {
  width_px: number;
  height_px: number;
  breakpoint: ResponsiveBreakpoint;
  layout_mode: LayoutMode;
  orientation: DeviceOrientation;
  navigation_adaptation: NavigationAdaptationType;
  modal_adaptation: ModalAdaptationType;
  filter_adaptation: FilterAdaptationType;
  outfit_builder_layout: OutfitBuilderLayoutType;
  map_layout: MapLayoutType;
  checkout_layout: CheckoutLayoutType;
  container_config: ResponsiveContainerContract;
  body_max_width_px: number;
  touch_target_px: number;
  supports_hover: boolean;
  is_compact: boolean;
  is_adaptive: boolean;
  is_expanded: boolean;
  is_touch: boolean;
  is_reduced_motion: boolean;
  safe_area_insets: SafeAreaInsetsContract;
}

export interface CrossSystemScreenResponsiveContract {
  screen_id: string;
  domain: string;
  title: string;
  layout_mode: LayoutMode;
  active_navigation: NavigationAdaptationType;
  content_density: string;
  has_sticky_actions: boolean;
  modal_presentation: ModalAdaptationType;
  filter_presentation: FilterAdaptationType;
  accessible_reading_order_preserved: boolean;
  touch_target_compliant: boolean;
  horizontal_overflow_prevented: boolean;
}
