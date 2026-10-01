/**
 * FashXStudio — Navigation Configuration (Phase 03)
 *
 * Canonical navigation items for the FashXStudio Application Shell.
 * Provides primary nav, personal nav, bottom bar slots, route-to-label
 * resolution, and breadcrumb builder (Sections 3.10, 3.14, 3.17).
 */

import type {
  BreadcrumbItem,
  NavigationConfig,
  NavigationItem,
  NavigationItemState,
  ShellLayoutMode,
  SidebarMode,
} from './types';

// ---------------------------------------------------------------------------
// Canonical Navigation Items
// ---------------------------------------------------------------------------

export const PRIMARY_NAV_ITEMS: NavigationItem[] = [
  { id: 'nav-home',     label: 'Home',     icon: 'home',     route: '/',         group: 'primary',  isVisible: true, requiresAuth: false, state: 'default' },
  { id: 'nav-discover', label: 'Discover', icon: 'compass',  route: '/discover', group: 'primary',  isVisible: true, requiresAuth: false, state: 'default' },
  { id: 'nav-search',   label: 'Search',   icon: 'search',   route: '/search',   group: 'primary',  isVisible: true, requiresAuth: false, state: 'default' },
  { id: 'nav-fashion',  label: 'Fashion',  icon: 'sparkles', route: '/fashion',  group: 'primary',  isVisible: true, requiresAuth: false, state: 'default' },
  { id: 'nav-shopping', label: 'Shopping', icon: 'bag',      route: '/shopping', group: 'primary',  isVisible: true, requiresAuth: false, state: 'default' },
  { id: 'nav-style',    label: 'Style',    icon: 'wand',     route: '/style',    group: 'primary',  isVisible: true, requiresAuth: false, state: 'default' },
  { id: 'nav-trends',   label: 'Trends',   icon: 'trending', route: '/trends',   group: 'primary',  isVisible: true, requiresAuth: false, state: 'default' },
  { id: 'nav-maps',     label: 'Maps',     icon: 'map',      route: '/maps',     group: 'primary',  isVisible: true, requiresAuth: false, state: 'default' },
  { id: 'nav-ai',       label: 'AI',       icon: 'cpu',      route: '/ai',       group: 'primary',  isVisible: true, requiresAuth: false, state: 'default' },
];

export const PERSONAL_NAV_ITEMS: NavigationItem[] = [
  { id: 'nav-saved',    label: 'Saved',    icon: 'bookmark', route: '/saved',    group: 'personal', isVisible: true, requiresAuth: true,  state: 'default' },
  { id: 'nav-wishlist', label: 'Wishlist', icon: 'heart',    route: '/wishlist', group: 'personal', isVisible: true, requiresAuth: true,  state: 'default' },
  { id: 'nav-profile',  label: 'Profile',  icon: 'person',   route: '/profile',  group: 'personal', isVisible: true, requiresAuth: true,  state: 'default' },
];

/** Mobile bottom navigation shows exactly 4 primary items + "Menu" trigger. */
export const BOTTOM_BAR_IDS: string[] = ['nav-home', 'nav-discover', 'nav-style', 'nav-saved'];

export const NAVIGATION_CONFIG: NavigationConfig = {
  primary: PRIMARY_NAV_ITEMS,
  personal: PERSONAL_NAV_ITEMS,
  bottomBarIds: BOTTOM_BAR_IDS,
};

// ---------------------------------------------------------------------------
// Active State Resolution
// ---------------------------------------------------------------------------

/**
 * Returns all navigation items with the correct state applied for a given active route.
 * Selected item = active route, all others = default.
 */
export function applyActiveRoute(
  config: NavigationConfig,
  activeRoute: string,
): NavigationConfig {
  const applyState = (items: NavigationItem[]): NavigationItem[] =>
    items.map((item) => ({
      ...item,
      state: (item.route === activeRoute ? 'selected' : 'default') as NavigationItemState,
    }));

  return {
    primary: applyState(config.primary),
    personal: applyState(config.personal),
    bottomBarIds: config.bottomBarIds,
  };
}

/** Returns items ordered for the mobile bottom navigation bar. */
export function getBottomBarItems(config: NavigationConfig): NavigationItem[] {
  const all = [...config.primary, ...config.personal];
  const idMap = new Map(all.map((i) => [i.id, i]));
  return config.bottomBarIds.flatMap((id) => (idMap.has(id) ? [idMap.get(id)!] : []));
}

// ---------------------------------------------------------------------------
// Layout Mode Resolution (Section 3.29)
// ---------------------------------------------------------------------------

/**
 * Resolves shell layout mode from viewport width.
 * Desktop >= 1024px | Tablet 768–1023px | Mobile < 768px
 */
export function resolveShellLayoutMode(viewportWidthPx: number): ShellLayoutMode {
  if (viewportWidthPx >= 1024) return 'desktop';
  if (viewportWidthPx >= 768) return 'tablet';
  return 'mobile';
}

export function resolveSidebarMode(viewportWidthPx: number): SidebarMode {
  if (viewportWidthPx >= 1280) return 'expanded';
  if (viewportWidthPx >= 1024) return 'collapsed';
  return 'hidden';
}

// ---------------------------------------------------------------------------
// Breadcrumb Builder (Section 3.17)
// ---------------------------------------------------------------------------

const ROUTE_LABELS: Record<string, string> = {
  '/': 'Home',
  '/discover': 'Discover',
  '/search': 'Search',
  '/fashion': 'Fashion',
  '/shopping': 'Shopping',
  '/style': 'Style',
  '/trends': 'Trends',
  '/maps': 'Maps',
  '/ai': 'AI',
  '/saved': 'Saved',
  '/wishlist': 'Wishlist',
  '/profile': 'Profile',
};

export function resolveBreadcrumbs(pathname: string): BreadcrumbItem[] {
  if (pathname === '/' || !pathname) {
    return [{ label: 'Home', route: '/', isCurrent: true }];
  }

  const breadcrumbs: BreadcrumbItem[] = [{ label: 'Home', route: '/', isCurrent: false }];
  const segments = pathname.split('/').filter(Boolean);
  let current = '';

  segments.forEach((segment, idx) => {
    current += `/${segment}`;
    const label =
      ROUTE_LABELS[current] ??
      segment.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    breadcrumbs.push({
      label,
      route: current,
      isCurrent: idx === segments.length - 1,
    });
  });

  return breadcrumbs;
}
