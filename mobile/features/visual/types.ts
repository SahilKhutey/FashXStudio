/**
 * FashXStudio — Visual Layer Type Definitions
 * Phase 00: Visual Design Development Foundation / Master Baseline
 * Phase 01: Visual Product Architecture + Complete Screen / Page Inventory
 */

export type ScreenDomain =
  | "platform"
  | "home"
  | "discovery"
  | "search"
  | "product"
  | "shopping"
  | "fashion"
  | "style"
  | "trends"
  | "regional"
  | "ai"
  | "profile"
  | "system"
  // Legacy aliases for backward compatibility
  | "onboarding"
  | "vto"
  | "closet"
  | "outfit"
  | "intelligence"
  | "admin";

export type PageTemplateType =
  | "listing"
  | "detail"
  | "discovery"
  | "editorial"
  | "builder"
  | "map"
  | "dashboard"
  | "assistant"
  | "comparison"
  | "checkout"
  | "settings";

export type ImplementationDependencyGroup =
  | "group_a_foundation"
  | "group_b_core_content"
  | "group_c_advanced_experiences"
  | "group_d_personalization"
  | "group_e_production_quality";

export type NavigationType = "tab" | "stack" | "modal" | "drawer";

export type DeviceBreakpoint = "xs" | "sm" | "md" | "lg" | "xl";

export type InteractionState =
  | "default"
  | "hover"
  | "focus"
  | "active"
  | "selected"
  | "disabled"
  | "loading"
  | "success"
  | "warning"
  | "error"
  | "empty"
  | "offline";

export type ComponentTaxonomyLevel =
  | "level_1_primitive"
  | "level_2_common_ui"
  | "level_3_domain"
  | "level_4_feature";

export type FashionContentType =
  | "product"
  | "outfit"
  | "look"
  | "style"
  | "trend"
  | "collection"
  | "brand"
  | "editorial"
  | "recommendation";

export type ShoppingFunnelStage =
  | "discover"
  | "understand"
  | "compare"
  | "select"
  | "save_cart"
  | "purchase_flow";

export type MapLayerType = "geographic" | "regional_data" | "fashion_shopping";

export type AiInteractionStage =
  | "user_input"
  | "processing"
  | "ai_result"
  | "explanation_context"
  | "user_controls"
  | "user_action";

export interface ScreenMetadata {
  id: string; // e.g. "P02", "D01", "SCR-DISC-01"
  screenCode?: string; // Short code e.g. "P02"
  title: string;
  domain: ScreenDomain;
  route: string;
  templateType: PageTemplateType;
  dependencyGroup: ImplementationDependencyGroup;
  navigationType: NavigationType;
  featureId: string; // e.g. "FX-F05"
  requiresAuth: boolean;
  requiresBiometricConsent: boolean;
  supportedBreakpoints: DeviceBreakpoint[];
  description: string;
}

/** 17-Point Screen Specification Contract (Visual Design — 0) */
export interface ScreenSpecificationContract {
  screenId: string;
  screenName: string;
  purpose: string;
  user: string;
  entryPoint: string;
  exitPoint: string;
  primaryAction: string;
  secondaryActions: string[];
  dataSources: string[];
  components: string[];
  states: InteractionState[];
  responsiveRules: Record<string, string>;
  accessibility: Record<string, string>;
  errorHandling: Record<string, string>;
  analyticsEvents: string[];
  dependencies: string[];
  testCases: string[];
}

export interface BreakpointMetrics {
  breakpoint: DeviceBreakpoint;
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  columns: number;
  gutter: number;
  margin: number;
  contentMaxWidth: number | null;
}

export interface NavigationTabItem {
  id: string;
  label: string;
  route: string;
  iconName: string;
  activeIconName: string;
  badgeCount?: number;
}

export interface BreadcrumbItem {
  label: string;
  route: string;
  isCurrent: boolean;
}

export interface UiStateEnvelope<T> {
  state: InteractionState;
  data: T | null;
  errorMessage: string | null;
  errorTraceId: string | null;
  isRetryable: boolean;
  emptyTitle?: string;
  emptyActionLabel?: string;
}
