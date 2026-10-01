/**
 * FashXStudio — Navigation Resolver (Phase 04)
 *
 * Route-to-navigation-state resolution engine (Section 4.1 & 4.2).
 * Implements Rule 02: Route is the single source of location truth.
 */

import type {
  BreadcrumbChain,
  BreadcrumbEntry,
  NavigationPresentation,
  NavigationResolverResult,
  NavigationState,
} from './types';
import { findActiveItem, evaluateAllGuards, ROUTE_REGISTRY } from './registry';
import { resolveShellLayoutMode } from '../shell/navigation';

// ---------------------------------------------------------------------------
// Route-to-Label Map (Section 4.14)
// ---------------------------------------------------------------------------

const ROUTE_LABELS: Record<string, string> = {
  '/': 'Home',
  '/discover': 'Discover',
  '/search': 'Search',
  '/fashion': 'Fashion',
  '/shopping': 'Shopping',
  '/shopping/products': 'Products',
  '/shopping/categories': 'Categories',
  '/shopping/cart': 'Cart',
  '/shopping/orders': 'Orders',
  '/style': 'Style',
  '/style/outfits': 'Outfit Builder',
  '/style/looks': 'Look Builder',
  '/style/saved': 'Saved Looks',
  '/style/preferences': 'Preferences',
  '/trends': 'Trends',
  '/maps': 'Maps',
  '/ai': 'AI',
  '/saved': 'Saved',
  '/wishlist': 'Wishlist',
  '/profile': 'Profile',
  '/profile/saved': 'Saved',
  '/profile/wishlist': 'Wishlist',
  '/profile/preferences': 'Preferences',
  '/profile/settings': 'Settings',
};

// ---------------------------------------------------------------------------
// Breadcrumb Builder (Section 4.14 & 4.15)
// ---------------------------------------------------------------------------

export function buildBreadcrumbChain(pathname: string): BreadcrumbChain {
  if (pathname === '/' || !pathname) {
    return {
      entries: [{ label: 'Home', route: '/', position: 1, isCurrent: true, isInteractive: false }],
      mobileLabel: 'Home',
      isTruncated: false,
    };
  }

  const entries: BreadcrumbEntry[] = [
    { label: 'Home', route: '/', position: 1, isCurrent: false, isInteractive: true },
  ];

  const segments = pathname.split('/').filter(Boolean);
  let current = '';

  segments.forEach((segment, idx) => {
    current += `/${segment}`;
    const isLast = idx === segments.length - 1;
    const label =
      ROUTE_LABELS[current] ??
      segment.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    entries.push({
      label,
      route: current,
      position: idx + 2,
      isCurrent: isLast,
      isInteractive: !isLast,
    });
  });

  const isTruncated = entries.length > 4;
  const mobileLabel = entries.length >= 2 ? entries[entries.length - 2].label : 'Home';

  return { entries, mobileLabel, isTruncated };
}

// ---------------------------------------------------------------------------
// Presentation Resolver (Section 4.34)
// ---------------------------------------------------------------------------

export function resolvePresentation(
  viewportWidthPx: number,
  sidebarCollapsed: boolean,
): NavigationPresentation {
  const mode = resolveShellLayoutMode(viewportWidthPx);
  if (mode === 'desktop') {
    return sidebarCollapsed ? 'desktop_collapsed' : 'desktop_expanded';
  }
  if (mode === 'tablet') return 'tablet';
  return 'mobile_header';
}

// ---------------------------------------------------------------------------
// Navigation State Builder (Section 4.37)
// ---------------------------------------------------------------------------

export function buildNavigationState(
  route: string,
  viewportWidthPx: number,
  options: {
    sidebarCollapsed?: boolean;
    mobileDrawerOpen?: boolean;
    navigationHistory?: string[];
  } = {},
): NavigationState {
  const { sidebarCollapsed = false, mobileDrawerOpen = false, navigationHistory = [] } = options;
  const { item: activeItem, parent: activeParent } = findActiveItem(ROUTE_REGISTRY, route);
  const presentation = resolvePresentation(viewportWidthPx, sidebarCollapsed);

  const expandedGroupIds: string[] = [];
  if (activeParent) expandedGroupIds.push(activeParent.id);
  else if (activeItem && activeItem.children.length > 0) expandedGroupIds.push(activeItem.id);

  return {
    currentRoute: route,
    activeItemId: activeItem?.id ?? null,
    activeParentId: activeParent?.id ?? null,
    expandedGroupIds,
    mobileDrawerOpen,
    sidebarCollapsed,
    focusedItemId: null,
    presentation,
    navigationHistory: navigationHistory.slice(-20),
  };
}

// ---------------------------------------------------------------------------
// Full Navigation Resolver (Section 4.1)
// ---------------------------------------------------------------------------

export function resolveNavigation(
  route: string,
  viewportWidthPx: number,
  options: {
    sidebarCollapsed?: boolean;
    activeFeatureFlags?: Set<string>;
    isAuthenticated?: boolean;
  } = {},
): NavigationResolverResult {
  const {
    sidebarCollapsed = false,
    activeFeatureFlags = new Set(),
    isAuthenticated = false,
  } = options;

  const { item: activeItem, parent: activeParent } = findActiveItem(ROUTE_REGISTRY, route);
  const breadcrumbChain = buildBreadcrumbChain(route);
  const navigationState = buildNavigationState(route, viewportWidthPx, { sidebarCollapsed });
  const guardResults = evaluateAllGuards(ROUTE_REGISTRY, activeFeatureFlags, isAuthenticated);

  return {
    route,
    activeItem,
    activeParent,
    breadcrumbChain,
    navigationState,
    guardResults,
  };
}
