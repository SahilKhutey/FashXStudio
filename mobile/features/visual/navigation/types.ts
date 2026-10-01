/**
 * FashXStudio — Navigation System Types (Phase 04)
 *
 * TypeScript contracts mirroring schemas/visual/navigation.py.
 * Covers: route registry, navigation state, tabs, context nav,
 * analytics events, guards, breadcrumbs, feature flags, error states.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type NavigationVisibility = 'visible' | 'hidden' | 'disabled' | 'restricted';

export type NavigationItemGroup = 'primary' | 'personal' | 'utility';

export type NavigationPresentation =
  | 'desktop_expanded'
  | 'desktop_collapsed'
  | 'tablet'
  | 'mobile_header'
  | 'mobile_drawer'
  | 'mobile_bottom';

export type TabMode = 'route_based' | 'state_based';

export type NestedNavExpansion = 'collapsed' | 'expanded' | 'active_child';

export type NavigationEventType =
  | 'navigation_view'
  | 'navigation_click'
  | 'navigation_open'
  | 'navigation_close'
  | 'breadcrumb_click'
  | 'tab_change'
  | 'back_navigation'
  | 'external_navigation'
  | 'search_navigation'
  | 'deep_link_entry'
  | 'navigation_error';

export type NavigationErrorCode =
  | 'not_found'
  | 'forbidden'
  | 'data_failure'
  | 'feature_disabled';

// ---------------------------------------------------------------------------
// Route Registry (Section 4.3 & 4.4)
// ---------------------------------------------------------------------------

export interface NavigationRoute {
  id: string;
  label: string;
  icon: string;
  route: string;
  group: NavigationItemGroup;
  order: number;
  visibility: NavigationVisibility;
  activeMatch: string[];
  isExternal: boolean;
  requiresAuth: boolean;
  featureFlag?: string;
  children: NavigationRoute[];
  metadata: Record<string, unknown>;
}

export interface RouteRegistry {
  routes: NavigationRoute[];
}

// ---------------------------------------------------------------------------
// Navigation State (Section 4.37)
// ---------------------------------------------------------------------------

export interface NavigationState {
  currentRoute: string;
  activeItemId: string | null;
  activeParentId: string | null;
  expandedGroupIds: string[];
  mobileDrawerOpen: boolean;
  sidebarCollapsed: boolean;
  focusedItemId: string | null;
  presentation: NavigationPresentation;
  navigationHistory: string[];
}

// ---------------------------------------------------------------------------
// Breadcrumbs (Section 4.14 & 4.15)
// ---------------------------------------------------------------------------

export interface BreadcrumbEntry {
  label: string;
  route: string;
  position: number;
  isCurrent: boolean;
  isInteractive: boolean;
}

export interface BreadcrumbChain {
  entries: BreadcrumbEntry[];
  mobileLabel: string;
  isTruncated: boolean;
}

// ---------------------------------------------------------------------------
// Tabs (Section 4.16, 4.17, 4.18)
// ---------------------------------------------------------------------------

export interface Tab {
  id: string;
  label: string;
  route?: string;
  stateKey?: string;
  isActive: boolean;
  isDisabled: boolean;
  badgeCount?: number;
  icon?: string;
}

export interface TabGroup {
  groupId: string;
  label?: string;
  mode: TabMode;
  tabs: Tab[];
}

// ---------------------------------------------------------------------------
// Context Navigation (Section 4.19 & 4.20)
// ---------------------------------------------------------------------------

export interface ContextNavItem {
  id: string;
  label: string;
  route?: string;
  stateKey?: string;
  isActive: boolean;
  isDisabled: boolean;
}

export interface ContextNavigation {
  contextId: string;
  label: string;
  items: ContextNavItem[];
  mode: TabMode;
}

// ---------------------------------------------------------------------------
// Analytics (Section 4.30)
// ---------------------------------------------------------------------------

export interface NavigationAnalyticsEvent {
  event: NavigationEventType;
  navigationId?: string;
  destination?: string;
  sourceRoute?: string;
  label?: string;
  metadata?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Guards (Section 4.28)
// ---------------------------------------------------------------------------

export interface NavigationGuardResult {
  itemId: string;
  visibility: NavigationVisibility;
  reason?: string;
  redirectRoute?: string;
}

// ---------------------------------------------------------------------------
// Feature Flags (Section 4.29)
// ---------------------------------------------------------------------------

export interface FeatureFlagNav {
  flagKey: string;
  isEnabled: boolean;
  itemId: string;
  resolvedVisibility: NavigationVisibility;
}

// ---------------------------------------------------------------------------
// Navigation Errors (Section 4.26 & 4.27)
// ---------------------------------------------------------------------------

export interface NavigationError {
  errorCode: NavigationErrorCode;
  attemptedRoute: string;
  userMessage: string;
  primaryRecoveryRoute: string;
  primaryRecoveryLabel: string;
  secondaryRecoveryRoute?: string;
  secondaryRecoveryLabel?: string;
}

// ---------------------------------------------------------------------------
// Resolver Result (Section 4.1)
// ---------------------------------------------------------------------------

export interface NavigationResolverResult {
  route: string;
  activeItem: NavigationRoute | null;
  activeParent: NavigationRoute | null;
  breadcrumbChain: BreadcrumbChain;
  navigationState: NavigationState;
  guardResults: NavigationGuardResult[];
}
