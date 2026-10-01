/**
 * FashXStudio — Application Shell Types (Phase 03)
 *
 * TypeScript contracts for the Application Shell navigation model,
 * layout modes, overlays, toast system, page headers, breadcrumbs,
 * and layout templates. Mirrors schemas/visual/shell.py contracts.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type NavigationGroup = 'primary' | 'personal' | 'utility';

export type NavigationItemState =
  | 'default'
  | 'hover'
  | 'focus'
  | 'active'
  | 'selected'
  | 'disabled';

export type SidebarMode = 'expanded' | 'collapsed' | 'hidden';

export type MobileDrawerState = 'open' | 'closed' | 'animating';

export type ShellLayoutMode = 'desktop' | 'tablet' | 'mobile';

export type PageHeaderVariant =
  | 'standard'
  | 'editorial'
  | 'listing'
  | 'detail'
  | 'dashboard';

export type LayoutTemplate =
  | 'standard'
  | 'listing'
  | 'detail'
  | 'editorial'
  | 'dashboard'
  | 'builder'
  | 'map'
  | 'assistant'
  | 'checkout';

export type OverlayType =
  | 'modal'
  | 'drawer'
  | 'popover'
  | 'command'
  | 'confirmation';

export type ToastType = 'success' | 'info' | 'warning' | 'error';

export type ShellLoadState = 'idle' | 'loading' | 'error' | 'ready';

// ---------------------------------------------------------------------------
// Navigation Model (Section 3.34)
// ---------------------------------------------------------------------------

export interface NavigationItem {
  id: string;
  label: string;
  icon: string;
  route: string;
  group: NavigationGroup;
  isVisible: boolean;
  requiresAuth: boolean;
  badgeCount?: number;
  state: NavigationItemState;
}

export interface NavigationConfig {
  primary: NavigationItem[];
  personal: NavigationItem[];
  bottomBarIds: string[];
}

// ---------------------------------------------------------------------------
// Shell Configuration
// ---------------------------------------------------------------------------

export interface AppHeaderConfig {
  brandName: string;
  brandLogoUri?: string;
  showSearch: boolean;
  showNotifications: boolean;
  showUserMenu: boolean;
  notificationCount: number;
  isSticky: boolean;
}

export interface ApplicationShellConfig {
  navigation: NavigationConfig;
  header: AppHeaderConfig;
  sidebarMode: SidebarMode;
  drawerState: MobileDrawerState;
  layoutMode: ShellLayoutMode;
  loadState: ShellLoadState;
  activeRoute: string;
  themeMode: 'light' | 'dark';
  skipNavTarget: string;
}

// ---------------------------------------------------------------------------
// Page Header & Breadcrumbs (Section 3.17)
// ---------------------------------------------------------------------------

export interface BreadcrumbItem {
  label: string;
  route: string;
  isCurrent: boolean;
}

export interface PageAction {
  label: string;
  actionId: string;
  variant: 'primary' | 'secondary' | 'ghost' | 'destructive';
  icon?: string;
  isDisabled?: boolean;
}

export interface PageHeader {
  variant: PageHeaderVariant;
  title: string;
  description?: string;
  breadcrumbs: BreadcrumbItem[];
  primaryAction?: PageAction;
  secondaryActions: PageAction[];
  statusLabel?: string;
  resultCount?: number;
  visualUri?: string;
}

// ---------------------------------------------------------------------------
// Layout Primitives (Section 3.20)
// ---------------------------------------------------------------------------

export interface ContentSection {
  sectionId: string;
  title?: string;
  description?: string;
  action?: PageAction;
  layout: 'grid' | 'list' | 'carousel' | 'stack';
  density: 'comfortable' | 'compact' | 'spacious';
}

export interface PageContainerConfig {
  maxWidth: string;
  horizontalPadding: string;
  useSidebarOffset: boolean;
}

export interface LayoutTemplateConfig {
  template: LayoutTemplate;
  pageHeader?: PageHeader;
  container: PageContainerConfig;
  sections: ContentSection[];
  isFullBleed: boolean;
  scrollBehavior: 'viewport' | 'feature-local' | 'none';
}

// ---------------------------------------------------------------------------
// Overlay & Toast (Section 3.21 & 3.22)
// ---------------------------------------------------------------------------

export interface Overlay {
  overlayId: string;
  overlayType: OverlayType;
  title?: string;
  isDismissible: boolean;
  hasFocusTrap: boolean;
}

export interface Toast {
  toastId: string;
  toastType: ToastType;
  message: string;
  actionLabel?: string;
  autoDismissMs: number;
  isPersistent: boolean;
}

export interface OverlayRegistry {
  activeOverlays: Overlay[];
  toastQueue: Toast[];
}
