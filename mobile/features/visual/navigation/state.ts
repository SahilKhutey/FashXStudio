/**
 * FashXStudio — Navigation State Management (Phase 04)
 *
 * Functional (immutable) navigation state operations (Section 4.37 & 4.38).
 * Navigation state is separate from feature state (products, fashion, AI, etc.).
 */

import type { NavigationState } from './types';

export const initialNavigationState: NavigationState = {
  currentRoute: '/',
  activeItemId: null,
  activeParentId: null,
  expandedGroupIds: [],
  mobileDrawerOpen: false,
  sidebarCollapsed: false,
  focusedItemId: null,
  presentation: 'mobile_header',
  navigationHistory: [],
};

// ---------------------------------------------------------------------------
// Immutable State Transformers
// ---------------------------------------------------------------------------

export function openMobileDrawer(state: NavigationState): NavigationState {
  return { ...state, mobileDrawerOpen: true };
}

export function closeMobileDrawer(state: NavigationState): NavigationState {
  return { ...state, mobileDrawerOpen: false };
}

export function toggleSidebarCollapsed(state: NavigationState): NavigationState {
  return { ...state, sidebarCollapsed: !state.sidebarCollapsed };
}

export function setSidebarCollapsed(
  state: NavigationState,
  collapsed: boolean,
): NavigationState {
  return { ...state, sidebarCollapsed: collapsed };
}

export function expandGroup(state: NavigationState, groupId: string): NavigationState {
  if (state.expandedGroupIds.includes(groupId)) return state;
  return { ...state, expandedGroupIds: [...state.expandedGroupIds, groupId] };
}

export function collapseGroup(state: NavigationState, groupId: string): NavigationState {
  return {
    ...state,
    expandedGroupIds: state.expandedGroupIds.filter((id) => id !== groupId),
  };
}

export function toggleGroup(state: NavigationState, groupId: string): NavigationState {
  return state.expandedGroupIds.includes(groupId)
    ? collapseGroup(state, groupId)
    : expandGroup(state, groupId);
}

export function setFocusedItem(
  state: NavigationState,
  itemId: string | null,
): NavigationState {
  return { ...state, focusedItemId: itemId };
}

export function navigateTo(state: NavigationState, route: string): NavigationState {
  const history = [...state.navigationHistory, state.currentRoute].slice(-20);
  return {
    ...state,
    currentRoute: route,
    mobileDrawerOpen: false, // Drawer closes on navigation (Section 4.12)
    navigationHistory: history,
  };
}

export function navigateBack(state: NavigationState): NavigationState {
  if (state.navigationHistory.length === 0) return state;
  const prev = state.navigationHistory[state.navigationHistory.length - 1];
  return {
    ...state,
    currentRoute: prev,
    navigationHistory: state.navigationHistory.slice(0, -1),
  };
}

export function hasPreviousRoute(state: NavigationState): boolean {
  return state.navigationHistory.length > 0;
}

export function getPreviousRoute(state: NavigationState): string | null {
  if (state.navigationHistory.length === 0) return null;
  return state.navigationHistory[state.navigationHistory.length - 1];
}
