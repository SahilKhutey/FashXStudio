/**
 * FashXStudio — Navigation Route Registry (Phase 04)
 *
 * Canonical route registry for the FashXStudio Navigation System (Section 4.3 & 4.4).
 * One unified registry serves desktop sidebar, tablet compact nav, mobile drawer,
 * and mobile bottom navigation — only the presentation changes (Section 4.2 Rule 01).
 */

import type {
  BreadcrumbChain,
  BreadcrumbEntry,
  ContextNavigation,
  ContextNavItem,
  FeatureFlagNav,
  NavigationGuardResult,
  NavigationPresentation,
  NavigationRoute,
  NavigationState,
  NavigationVisibility,
  RouteRegistry,
  Tab,
  TabGroup,
} from './types';

// ---------------------------------------------------------------------------
// Route Registry Data (Section 4.3)
// ---------------------------------------------------------------------------

function route(
  id: string,
  label: string,
  icon: string,
  path: string,
  group: 'primary' | 'personal',
  order: number,
  opts: Partial<Omit<NavigationRoute, 'id' | 'label' | 'icon' | 'route' | 'group' | 'order'>> = {},
): NavigationRoute {
  return {
    id,
    label,
    icon,
    route: path,
    group,
    order,
    visibility: 'visible',
    activeMatch: [],
    isExternal: false,
    requiresAuth: false,
    children: [],
    metadata: {},
    ...opts,
  };
}

export const ROUTE_REGISTRY: RouteRegistry = {
  routes: [
    // --- PRIMARY ---
    route('nav-home',     'Home',     'home',     '/',         'primary', 1, { activeMatch: ['/(tabs)/discover'] }),
    route('nav-discover', 'Discover', 'compass',  '/discover', 'primary', 2, { activeMatch: ['/discover/'] }),
    route('nav-search',   'Search',   'search',   '/search',   'primary', 3),
    route('nav-fashion',  'Fashion',  'sparkles', '/fashion',  'primary', 4, { activeMatch: ['/fashion/'] }),
    route('nav-shopping', 'Shopping', 'bag',      '/shopping', 'primary', 5, {
      activeMatch: ['/shopping/'],
      children: [
        route('nav-shopping-products',   'All Products', 'grid',     '/shopping/products',   'primary', 1),
        route('nav-shopping-categories', 'Categories',   'layers',   '/shopping/categories', 'primary', 2),
        route('nav-shopping-cart',       'Cart',         'cart',     '/shopping/cart',       'primary', 3, { requiresAuth: true }),
        route('nav-shopping-orders',     'Orders',       'box',      '/shopping/orders',     'primary', 4, { requiresAuth: true }),
      ],
    }),
    route('nav-style', 'Style', 'wand', '/style', 'primary', 6, {
      activeMatch: ['/style/'],
      children: [
        route('nav-style-home',    'Style Home',    'home',     '/style',             'primary', 1),
        route('nav-style-outfits', 'Outfit Builder','tool',     '/style/outfits',     'primary', 2),
        route('nav-style-looks',   'Look Builder',  'image',    '/style/looks',       'primary', 3),
        route('nav-style-saved',   'Saved Looks',   'bookmark', '/style/saved',       'primary', 4, { requiresAuth: true }),
        route('nav-style-prefs',   'Preferences',   'sliders',  '/style/preferences', 'primary', 5, { requiresAuth: true }),
      ],
    }),
    route('nav-trends', 'Trends', 'trending', '/trends', 'primary', 7, { activeMatch: ['/trends/'] }),
    route('nav-maps',   'Maps',   'map',      '/maps',   'primary', 8, { activeMatch: ['/maps/'] }),
    route('nav-ai',     'AI',     'cpu',      '/ai',     'primary', 9, { activeMatch: ['/ai/'] }),
    // --- PERSONAL ---
    route('nav-saved',    'Saved',    'bookmark', '/saved',    'personal', 1, { requiresAuth: true }),
    route('nav-wishlist', 'Wishlist', 'heart',    '/wishlist', 'personal', 2, { requiresAuth: true }),
    route('nav-profile',  'Profile',  'person',   '/profile',  'personal', 3, {
      requiresAuth: true,
      children: [
        route('nav-profile-overview', 'Overview',    'user',     '/profile',              'personal', 1, { requiresAuth: true }),
        route('nav-profile-saved',    'Saved',       'bookmark', '/profile/saved',        'personal', 2, { requiresAuth: true }),
        route('nav-profile-wishlist', 'Wishlist',    'heart',    '/profile/wishlist',     'personal', 3, { requiresAuth: true }),
        route('nav-profile-prefs',    'Preferences', 'sliders',  '/profile/preferences',  'personal', 4, { requiresAuth: true }),
        route('nav-profile-settings', 'Settings',    'settings', '/profile/settings',     'personal', 5, { requiresAuth: true }),
      ],
    }),
  ],
};

// ---------------------------------------------------------------------------
// Registry Helpers
// ---------------------------------------------------------------------------

export function flatRoutes(registry: RouteRegistry): NavigationRoute[] {
  return registry.routes.flatMap((r) => [r, ...r.children]);
}

export function findByRoute(registry: RouteRegistry, route: string): NavigationRoute | null {
  for (const r of registry.routes) {
    if (r.route === route || r.activeMatch.includes(route)) return r;
    for (const child of r.children) {
      if (child.route === route || child.activeMatch.includes(route)) return child;
    }
  }
  return null;
}

export function findById(registry: RouteRegistry, id: string): NavigationRoute | null {
  return flatRoutes(registry).find((r) => r.id === id) ?? null;
}

export function findParent(
  registry: RouteRegistry,
  childId: string,
): NavigationRoute | null {
  for (const r of registry.routes) {
    if (r.children.some((c) => c.id === childId)) return r;
  }
  return null;
}

/** Returns primary nav items sorted by order */
export function primaryRoutes(registry: RouteRegistry): NavigationRoute[] {
  return registry.routes
    .filter((r) => r.group === 'primary')
    .sort((a, b) => a.order - b.order);
}

/** Returns personal nav items sorted by order */
export function personalRoutes(registry: RouteRegistry): NavigationRoute[] {
  return registry.routes
    .filter((r) => r.group === 'personal')
    .sort((a, b) => a.order - b.order);
}

// ---------------------------------------------------------------------------
// Active Route Resolution (Section 4.2 Rule 02)
// ---------------------------------------------------------------------------

function matchesRoute(item: NavigationRoute, currentRoute: string): boolean {
  if (item.route === currentRoute) return true;
  if (item.activeMatch.includes(currentRoute)) return true;
  if (item.route !== '/' && currentRoute.startsWith(item.route + '/')) return true;
  return false;
}

export function findActiveItem(
  registry: RouteRegistry,
  currentRoute: string,
): { item: NavigationRoute | null; parent: NavigationRoute | null } {
  for (const r of registry.routes) {
    for (const child of r.children) {
      if (matchesRoute(child, currentRoute)) return { item: child, parent: r };
    }
    if (matchesRoute(r, currentRoute)) return { item: r, parent: null };
  }
  return { item: null, parent: null };
}

// ---------------------------------------------------------------------------
// Navigation Guards (Section 4.28 & 4.29)
// ---------------------------------------------------------------------------

export function evaluateItemVisibility(
  item: NavigationRoute,
  activeFeatureFlags: Set<string>,
  isAuthenticated: boolean,
): NavigationGuardResult {
  if (item.featureFlag && !activeFeatureFlags.has(item.featureFlag)) {
    return { itemId: item.id, visibility: 'hidden', reason: `Feature flag '${item.featureFlag}' disabled` };
  }
  if (item.requiresAuth && !isAuthenticated) {
    return { itemId: item.id, visibility: 'restricted', reason: 'Authentication required', redirectRoute: '/auth/login' };
  }
  return { itemId: item.id, visibility: item.visibility };
}

export function evaluateAllGuards(
  registry: RouteRegistry,
  activeFeatureFlags: Set<string>,
  isAuthenticated: boolean,
): NavigationGuardResult[] {
  return flatRoutes(registry).map((item) =>
    evaluateItemVisibility(item, activeFeatureFlags, isAuthenticated),
  );
}

export function resolveFeatureFlag(
  item: NavigationRoute,
  activeFeatureFlags: Set<string>,
): FeatureFlagNav {
  if (!item.featureFlag) {
    return { flagKey: '', isEnabled: true, itemId: item.id, resolvedVisibility: item.visibility };
  }
  const isEnabled = activeFeatureFlags.has(item.featureFlag);
  return {
    flagKey: item.featureFlag,
    isEnabled,
    itemId: item.id,
    resolvedVisibility: isEnabled ? 'visible' : 'hidden',
  };
}
