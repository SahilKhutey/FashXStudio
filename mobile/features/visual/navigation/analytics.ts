/**
 * FashXStudio — Navigation Analytics (Phase 04)
 *
 * Structured navigation event builders (Section 4.30).
 * Uses the existing FashXStudio analytics infrastructure via platform/api.ts.
 */

import type { NavigationAnalyticsEvent, NavigationEventType } from './types';

// ---------------------------------------------------------------------------
// Event Builders
// ---------------------------------------------------------------------------

export function buildNavEvent(
  event: NavigationEventType,
  opts: Partial<Omit<NavigationAnalyticsEvent, 'event'>> = {},
): NavigationAnalyticsEvent {
  return { event, ...opts };
}

export const navEvents = {
  view: (route: string, itemId?: string) =>
    buildNavEvent('navigation_view', { navigationId: itemId, destination: route }),

  click: (itemId: string, destination: string, sourceRoute?: string) =>
    buildNavEvent('navigation_click', { navigationId: itemId, destination, sourceRoute }),

  open: (itemId: string) =>
    buildNavEvent('navigation_open', { navigationId: itemId }),

  close: (itemId: string) =>
    buildNavEvent('navigation_close', { navigationId: itemId }),

  breadcrumbClick: (route: string, label: string, position: number) =>
    buildNavEvent('breadcrumb_click', { destination: route, label, metadata: { position } }),

  tabChange: (groupId: string, tabId: string, destination: string) =>
    buildNavEvent('tab_change', { navigationId: tabId, destination, metadata: { groupId } }),

  back: (fromRoute: string, toRoute: string) =>
    buildNavEvent('back_navigation', { sourceRoute: fromRoute, destination: toRoute }),

  external: (destination: string, sourceRoute: string, label?: string) =>
    buildNavEvent('external_navigation', { destination, sourceRoute, label }),

  search: (query: string, sourceRoute: string) =>
    buildNavEvent('search_navigation', { destination: `/search?q=${encodeURIComponent(query)}`, sourceRoute }),

  deepLink: (destination: string) =>
    buildNavEvent('deep_link_entry', { destination }),

  error: (attemptedRoute: string, errorCode: string) =>
    buildNavEvent('navigation_error', {
      destination: attemptedRoute,
      metadata: { errorCode },
    }),
} as const;
