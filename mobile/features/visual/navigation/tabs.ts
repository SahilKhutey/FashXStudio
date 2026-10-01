/**
 * FashXStudio — Tab & Context Navigation Utilities (Phase 04)
 *
 * Tab group builders (route-based and state-based) and context navigation
 * management for per-page/section navigation (Sections 4.16–4.20).
 */

import type { ContextNavigation, ContextNavItem, Tab, TabGroup, TabMode } from './types';

// ---------------------------------------------------------------------------
// Well-Known Tab Groups (Section 4.16 & 4.18)
// ---------------------------------------------------------------------------

/** Product detail tabs — route-based (Section 4.18) */
export const PRODUCT_TABS_TEMPLATE: Omit<Tab, 'isActive'>[] = [
  { id: 'tab-overview',  label: 'Overview',   route: '/products/{id}',               isDisabled: false },
  { id: 'tab-reviews',   label: 'Reviews',    route: '/products/{id}/reviews',       isDisabled: false },
  { id: 'tab-specs',     label: 'Specs',      route: '/products/{id}/specifications',isDisabled: false },
  { id: 'tab-styling',   label: 'Styling',    route: '/products/{id}/styling',       isDisabled: false },
];

/** Profile context navigation — route-based (Section 4.19) */
export const PROFILE_CONTEXT_ITEMS: Omit<ContextNavItem, 'isActive'>[] = [
  { id: 'ctx-profile-overview', label: 'Overview',    route: '/profile',              isDisabled: false },
  { id: 'ctx-profile-saved',    label: 'Saved',       route: '/profile/saved',        isDisabled: false },
  { id: 'ctx-profile-wishlist', label: 'Wishlist',    route: '/profile/wishlist',     isDisabled: false },
  { id: 'ctx-profile-prefs',    label: 'Preferences', route: '/profile/preferences',  isDisabled: false },
  { id: 'ctx-profile-settings', label: 'Settings',    route: '/profile/settings',     isDisabled: false },
];

// ---------------------------------------------------------------------------
// Tab Group Builder
// ---------------------------------------------------------------------------

export function buildProductTabs(productId: string, activeRoute: string): TabGroup {
  const tabs: Tab[] = PRODUCT_TABS_TEMPLATE.map((t) => {
    const resolvedRoute = t.route?.replace('{id}', productId);
    return { ...t, route: resolvedRoute, isActive: resolvedRoute === activeRoute };
  });
  return {
    groupId: 'product-detail-tabs',
    label: 'Product details',
    mode: 'route_based',
    tabs,
  };
}

export function buildTabGroup(
  groupId: string,
  mode: TabMode,
  tabs: Tab[],
  label?: string,
): TabGroup {
  return { groupId, label, mode, tabs };
}

export function setActiveTab(group: TabGroup, tabId: string): TabGroup {
  return {
    ...group,
    tabs: group.tabs.map((t) => ({ ...t, isActive: t.id === tabId })),
  };
}

export function setActiveTabByRoute(group: TabGroup, currentRoute: string): TabGroup {
  return {
    ...group,
    tabs: group.tabs.map((t) => ({ ...t, isActive: t.route === currentRoute })),
  };
}

// ---------------------------------------------------------------------------
// Context Navigation Builder
// ---------------------------------------------------------------------------

export function buildContextNavigation(
  contextId: string,
  label: string,
  items: Omit<ContextNavItem, 'isActive'>[],
  activeRoute: string,
  mode: TabMode = 'route_based',
): ContextNavigation {
  return {
    contextId,
    label,
    mode,
    items: items.map((item) => ({
      ...item,
      isActive: item.route === activeRoute,
    })),
  };
}

export function buildProfileContextNav(activeRoute: string): ContextNavigation {
  return buildContextNavigation(
    'profile-context-nav',
    'Profile navigation',
    PROFILE_CONTEXT_ITEMS,
    activeRoute,
  );
}

export function getActiveItem(ctx: ContextNavigation): ContextNavItem | undefined {
  return ctx.items.find((i) => i.isActive);
}
