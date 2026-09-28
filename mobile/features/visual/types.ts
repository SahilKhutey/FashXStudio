/**
 * FashXStudio — Visual Layer Type Definitions
 * Phase 00: Visual Design Development Foundation / Master Baseline
 * Phase 01: Visual Product Architecture
 */

export type ScreenDomain =
  | "onboarding"
  | "discovery"
  | "search"
  | "product"
  | "vto"
  | "closet"
  | "outfit"
  | "shopping"
  | "regional"
  | "intelligence"
  | "profile"
  | "admin";

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
  id: string; // e.g. "SCR-DISC-01"
  title: string;
  domain: ScreenDomain;
  route: string;
  navigationType: NavigationType;
  featureId: string; // e.g. "FX-F03"
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
