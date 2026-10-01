/**
 * FashXStudio — Application Shell React Native Components (Phase 03)
 *
 * Implements the production Application Shell infrastructure for React Native / Expo Router:
 * - ApplicationShell: root layout wrapper with layout mode and provider
 * - AppHeader: global header with brand, search trigger, notifications, user
 * - MobileBottomNavigation: bottom tab bar for xs/sm viewports
 * - MobileNavigationDrawer: full navigation drawer with focus management
 * - PageContainer: responsive max-width container with gutter
 * - PageHeaderBlock: standardized page header (standard, listing, detail, editorial)
 * - ContentSection: reusable section wrapper with title and action
 * - SkipNavigation: accessibility skip link
 * - ShellLoadingState: structural skeleton for shell-level loading
 * - ShellErrorState: human-readable error with retry
 *
 * All style values consume Phase 02 design tokens.
 * All containers respect Phase 02 spacing and breakpoint tokens.
 */

import React, {
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  AccessibilityInfo,
  Animated,
  BackHandler,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  neutralPrimitives,
  brandPalette,
  spacingScale,
  radiusScale,
  elevationShadows,
  zIndexScale,
  typeScale,
} from '../tokens/primitives';
import {
  lightSemanticSurfaces,
  lightSemanticContent,
  lightSemanticBorders,
  lightSemanticActions,
} from '../tokens/semantic';
import { resolveShellLayoutMode, resolveSidebarMode, getBottomBarItems } from './navigation';
import type {
  ApplicationShellConfig,
  BreadcrumbItem,
  ContentSection,
  NavigationConfig,
  NavigationItem,
  PageHeader,
  ShellLayoutMode,
  SidebarMode,
  Toast,
} from './types';

// ============================================================================
// SkipNavigation (Section 3.23)
// ============================================================================

export function SkipNavigation() {
  // On native platforms, skip navigation is handled by VoiceOver/TalkBack ordering.
  // This renders the ARIA-equivalent accessible label announcement region.
  return (
    <View accessibilityRole="none" accessible={false} style={styles.skipNav}>
      <Text
        accessible={true}
        accessibilityLabel="Skip to main content"
        style={styles.skipNavText}
      >
        Skip to main content
      </Text>
    </View>
  );
}

// ============================================================================
// AppHeader (Section 3.8)
// ============================================================================

interface AppHeaderProps {
  brandName?: string;
  notificationCount?: number;
  showSearch?: boolean;
  showNotifications?: boolean;
  showUserMenu?: boolean;
  onSearchPress?: () => void;
  onNotificationsPress?: () => void;
  onUserMenuPress?: () => void;
  onMenuPress?: () => void; // Mobile: opens drawer
  layoutMode: ShellLayoutMode;
}

export function AppHeader({
  brandName = 'FashXStudio',
  notificationCount = 0,
  showSearch = true,
  showNotifications = true,
  showUserMenu = true,
  onSearchPress,
  onNotificationsPress,
  onUserMenuPress,
  onMenuPress,
  layoutMode,
}: AppHeaderProps) {
  const insets = useSafeAreaInsets();
  const isMobile = layoutMode === 'mobile';

  return (
    <View
      style={[styles.header, { paddingTop: insets.top + 8 }]}
      accessibilityRole="banner"
      accessible={true}
      accessibilityLabel="FashXStudio application header"
    >
      {/* Mobile: menu button | Desktop: logo */}
      <View style={styles.headerLeft}>
        {isMobile && onMenuPress && (
          <TouchableOpacity
            onPress={onMenuPress}
            style={styles.headerIconButton}
            accessibilityRole="button"
            accessibilityLabel="Open navigation menu"
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={styles.headerIconText}>☰</Text>
          </TouchableOpacity>
        )}
        <Text style={styles.brandName} accessibilityRole="header">
          {brandName}
        </Text>
      </View>

      {/* Search bar (desktop only inline, mobile shows icon) */}
      {showSearch && (
        <TouchableOpacity
          onPress={onSearchPress}
          style={[styles.searchBar, isMobile ? styles.searchBarMobile : styles.searchBarDesktop]}
          accessibilityRole="search"
          accessibilityLabel="Search products, styles, and trends"
        >
          <Text style={styles.searchIcon}>🔍</Text>
          {!isMobile && (
            <Text style={styles.searchPlaceholder}>
              Search products, styles, trends…
            </Text>
          )}
        </TouchableOpacity>
      )}

      {/* Right controls */}
      <View style={styles.headerRight}>
        {showNotifications && (
          <TouchableOpacity
            onPress={onNotificationsPress}
            style={styles.headerIconButton}
            accessibilityRole="button"
            accessibilityLabel={`Notifications${notificationCount > 0 ? `, ${notificationCount} unread` : ''}`}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={styles.headerIconText}>🔔</Text>
            {notificationCount > 0 && (
              <View style={styles.badge}>
                <Text style={styles.badgeText}>
                  {notificationCount > 9 ? '9+' : notificationCount}
                </Text>
              </View>
            )}
          </TouchableOpacity>
        )}
        {showUserMenu && (
          <TouchableOpacity
            onPress={onUserMenuPress}
            style={styles.headerIconButton}
            accessibilityRole="button"
            accessibilityLabel="User account menu"
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>U</Text>
            </View>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

// ============================================================================
// MobileBottomNavigation (Section 3.14)
// ============================================================================

interface MobileBottomNavigationProps {
  navConfig: NavigationConfig;
  activeRoute: string;
  onNavigate: (route: string) => void;
  onMenuPress: () => void;
}

export function MobileBottomNavigation({
  navConfig,
  activeRoute,
  onNavigate,
  onMenuPress,
}: MobileBottomNavigationProps) {
  const insets = useSafeAreaInsets();
  const bottomBarItems = getBottomBarItems(navConfig);

  const iconMap: Record<string, string> = {
    home: '🏠', compass: '🧭', search: '🔍', sparkles: '✨',
    bag: '🛍', wand: '🪄', trending: '📈', map: '🗺', cpu: '🤖',
    bookmark: '🔖', heart: '❤️', person: '👤',
  };

  return (
    <View
      style={[styles.bottomNav, { paddingBottom: insets.bottom + 4 }]}
      accessibilityRole="tablist"
      accessibilityLabel="Primary navigation"
    >
      {bottomBarItems.map((item) => {
        const isActive = item.route === activeRoute;
        return (
          <TouchableOpacity
            key={item.id}
            onPress={() => onNavigate(item.route)}
            style={styles.bottomNavItem}
            accessibilityRole="tab"
            accessibilityLabel={item.label}
            accessibilityState={{ selected: isActive }}
          >
            <Text style={[styles.bottomNavIcon, isActive && styles.bottomNavIconActive]}>
              {iconMap[item.icon] ?? '●'}
            </Text>
            <Text style={[styles.bottomNavLabel, isActive && styles.bottomNavLabelActive]}>
              {item.label}
            </Text>
          </TouchableOpacity>
        );
      })}

      {/* Menu trigger (Section 3.14 — 5th slot = Menu) */}
      <TouchableOpacity
        onPress={onMenuPress}
        style={styles.bottomNavItem}
        accessibilityRole="button"
        accessibilityLabel="Open full navigation menu"
      >
        <Text style={styles.bottomNavIcon}>☰</Text>
        <Text style={styles.bottomNavLabel}>Menu</Text>
      </TouchableOpacity>
    </View>
  );
}

// ============================================================================
// MobileNavigationDrawer (Section 3.13)
// ============================================================================

interface MobileNavigationDrawerProps {
  isOpen: boolean;
  navConfig: NavigationConfig;
  activeRoute: string;
  onClose: () => void;
  onNavigate: (route: string) => void;
}

export function MobileNavigationDrawer({
  isOpen,
  navConfig,
  activeRoute,
  onClose,
  onNavigate,
}: MobileNavigationDrawerProps) {
  const slideAnim = useRef(new Animated.Value(-300)).current;

  useEffect(() => {
    Animated.timing(slideAnim, {
      toValue: isOpen ? 0 : -300,
      duration: 250,
      useNativeDriver: true,
    }).start();
  }, [isOpen, slideAnim]);

  // Hardware back button closes drawer (Section 3.13)
  useEffect(() => {
    if (!isOpen) return;
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      onClose();
      return true;
    });
    return () => sub.remove();
  }, [isOpen, onClose]);

  const handleNavigate = useCallback(
    (route: string) => {
      onClose();
      onNavigate(route);
    },
    [onClose, onNavigate],
  );

  const iconMap: Record<string, string> = {
    home: '🏠', compass: '🧭', search: '🔍', sparkles: '✨',
    bag: '🛍', wand: '🪄', trending: '📈', map: '🗺', cpu: '🤖',
    bookmark: '🔖', heart: '❤️', person: '👤',
  };

  const renderNavItem = (item: NavigationItem) => {
    const isActive = item.route === activeRoute;
    return (
      <TouchableOpacity
        key={item.id}
        onPress={() => handleNavigate(item.route)}
        style={[styles.drawerItem, isActive && styles.drawerItemActive]}
        accessibilityRole="menuitem"
        accessibilityLabel={item.label}
        accessibilityState={{ selected: isActive }}
      >
        <Text style={styles.drawerItemIcon}>{iconMap[item.icon] ?? '●'}</Text>
        <Text style={[styles.drawerItemLabel, isActive && styles.drawerItemLabelActive]}>
          {item.label}
        </Text>
      </TouchableOpacity>
    );
  };

  if (!isOpen) return null;

  return (
    <Modal
      visible={isOpen}
      transparent
      animationType="none"
      onRequestClose={onClose}
      accessibilityViewIsModal={true}
    >
      {/* Scrim backdrop */}
      <Pressable style={styles.drawerScrim} onPress={onClose} accessible={false} />

      {/* Drawer panel */}
      <Animated.View
        style={[styles.drawerPanel, { transform: [{ translateX: slideAnim }] }]}
        accessibilityRole="menu"
        accessibilityLabel="Navigation menu"
      >
        {/* Drawer header */}
        <View style={styles.drawerHeader}>
          <Text style={styles.drawerBrand}>FashXStudio</Text>
          <TouchableOpacity
            onPress={onClose}
            style={styles.drawerClose}
            accessibilityRole="button"
            accessibilityLabel="Close navigation menu"
          >
            <Text style={styles.drawerCloseText}>✕</Text>
          </TouchableOpacity>
        </View>

        <ScrollView showsVerticalScrollIndicator={false}>
          {/* Primary navigation */}
          <View style={styles.drawerGroup}>
            {navConfig.primary.map(renderNavItem)}
          </View>

          {/* Divider */}
          <View style={styles.drawerDivider} />

          {/* Personal navigation */}
          <View style={styles.drawerGroup}>
            {navConfig.personal.map(renderNavItem)}
          </View>
        </ScrollView>
      </Animated.View>
    </Modal>
  );
}

// ============================================================================
// PageContainer (Section 3.16)
// ============================================================================

interface PageContainerProps {
  children: ReactNode;
  maxWidth?: number;
  padded?: boolean;
  scrollable?: boolean;
}

export function PageContainer({
  children,
  maxWidth = 1280,
  padded = true,
  scrollable = true,
}: PageContainerProps) {
  const { width } = useWindowDimensions();
  const effectiveWidth = Math.min(width, maxWidth);
  const gutterPx = width >= 1024 ? spacingScale.space8 : width >= 768 ? spacingScale.space6 : spacingScale.space4;

  const containerStyle = [
    styles.pageContainer,
    padded && { paddingHorizontal: gutterPx },
    effectiveWidth < width && { width: effectiveWidth, alignSelf: 'center' as const },
  ];

  if (scrollable) {
    return (
      <ScrollView
        style={styles.pageContainerScroll}
        contentContainerStyle={containerStyle}
        keyboardShouldPersistTaps="handled"
        accessibilityRole="main"
        accessibilityLabel="Main content"
      >
        {children}
      </ScrollView>
    );
  }

  return (
    <View
      style={containerStyle}
      accessibilityRole="main"
      accessibilityLabel="Main content"
    >
      {children}
    </View>
  );
}

// ============================================================================
// PageHeaderBlock (Section 3.17 & 3.18)
// ============================================================================

interface PageHeaderBlockProps {
  pageHeader: PageHeader;
  onActionPress?: (actionId: string) => void;
}

export function PageHeaderBlock({ pageHeader, onActionPress }: PageHeaderBlockProps) {
  return (
    <View style={styles.pageHeader} accessibilityRole="none">
      {/* Breadcrumbs */}
      {pageHeader.breadcrumbs.length > 1 && (
        <View style={styles.breadcrumbs} accessibilityRole="none">
          {pageHeader.breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={crumb.route}>
              <Text
                style={[styles.breadcrumbItem, crumb.isCurrent && styles.breadcrumbCurrent]}
                accessibilityLabel={crumb.isCurrent ? `${crumb.label}, current page` : crumb.label}
              >
                {crumb.label}
              </Text>
              {!crumb.isCurrent && <Text style={styles.breadcrumbSep}> / </Text>}
            </React.Fragment>
          ))}
        </View>
      )}

      {/* Title row */}
      <View style={styles.pageHeaderTitleRow}>
        <Text
          style={[
            styles.pageHeaderTitle,
            pageHeader.variant === 'editorial' && styles.pageHeaderTitleEditorial,
          ]}
          accessibilityRole="header"
        >
          {pageHeader.title}
        </Text>
        {pageHeader.primaryAction && (
          <TouchableOpacity
            onPress={() => onActionPress?.(pageHeader.primaryAction!.actionId)}
            style={styles.pageHeaderAction}
            disabled={pageHeader.primaryAction.isDisabled}
            accessibilityRole="button"
            accessibilityLabel={pageHeader.primaryAction.label}
          >
            <Text style={styles.pageHeaderActionText}>{pageHeader.primaryAction.label}</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Description */}
      {pageHeader.description && (
        <Text style={styles.pageHeaderDescription}>{pageHeader.description}</Text>
      )}

      {/* Listing: result count */}
      {pageHeader.resultCount !== undefined && (
        <Text style={styles.pageHeaderResultCount}>{pageHeader.resultCount} results</Text>
      )}
    </View>
  );
}

// ============================================================================
// ContentSection (Section 3.19)
// ============================================================================

interface ContentSectionProps {
  section: ContentSection;
  children: ReactNode;
  onActionPress?: (actionId: string) => void;
}

export function ContentSectionWrapper({ section, children, onActionPress }: ContentSectionProps) {
  return (
    <View style={styles.contentSection} accessibilityRole="region" accessibilityLabel={section.title}>
      {(section.title || section.action) && (
        <View style={styles.sectionHeader}>
          {section.title && <Text style={styles.sectionTitle}>{section.title}</Text>}
          {section.action && (
            <TouchableOpacity
              onPress={() => onActionPress?.(section.action!.actionId)}
              accessibilityRole="button"
              accessibilityLabel={section.action.label}
            >
              <Text style={styles.sectionAction}>{section.action.label} →</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
      {section.description && <Text style={styles.sectionDescription}>{section.description}</Text>}
      {children}
    </View>
  );
}

// ============================================================================
// ToastRegion (Section 3.22)
// ============================================================================

interface ToastRegionProps {
  toasts: Toast[];
  onDismiss: (toastId: string) => void;
}

const TOAST_ICONS: Record<string, string> = {
  success: '✓', info: 'ℹ', warning: '⚠', error: '✕',
};

const TOAST_COLORS: Record<string, string> = {
  success: '#10B981', info: '#3B82F6', warning: '#F59E0B', error: '#EF4444',
};

export function ToastRegion({ toasts, onDismiss }: ToastRegionProps) {
  if (toasts.length === 0) return null;
  return (
    <View style={styles.toastRegion} accessibilityRole="status" accessibilityLiveRegion="polite">
      {toasts.map((toast) => (
        <View
          key={toast.toastId}
          style={[styles.toast, { borderLeftColor: TOAST_COLORS[toast.toastType] }]}
          accessibilityRole="alert"
        >
          <Text style={[styles.toastIcon, { color: TOAST_COLORS[toast.toastType] }]}>
            {TOAST_ICONS[toast.toastType]}
          </Text>
          <Text style={styles.toastMessage}>{toast.message}</Text>
          {!toast.isPersistent && (
            <TouchableOpacity
              onPress={() => onDismiss(toast.toastId)}
              accessibilityRole="button"
              accessibilityLabel="Dismiss notification"
            >
              <Text style={styles.toastDismiss}>✕</Text>
            </TouchableOpacity>
          )}
        </View>
      ))}
    </View>
  );
}

// ============================================================================
// ShellLoadingState (Section 3.27)
// ============================================================================

export function ShellLoadingState() {
  const pulseAnim = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 0.3, duration: 800, useNativeDriver: true }),
      ]),
    );
    animation.start();
    return () => animation.stop();
  }, [pulseAnim]);

  const skeletonStyle = { opacity: pulseAnim, backgroundColor: neutralPrimitives.neutral200 };

  return (
    <View style={styles.shellLoadingRoot} accessibilityLabel="Loading…" accessibilityLiveRegion="polite">
      {/* Header skeleton */}
      <View style={styles.headerSkeleton}>
        <Animated.View style={[styles.skeletonBlock, { width: 120, height: 20 }, skeletonStyle]} />
        <Animated.View style={[styles.skeletonBlock, { flex: 1, marginHorizontal: 16, height: 36 }, skeletonStyle]} />
        <Animated.View style={[styles.skeletonBlock, { width: 36, height: 36, borderRadius: 18 }, skeletonStyle]} />
      </View>
      {/* Content skeletons */}
      {[100, 80, 90, 70].map((w, i) => (
        <Animated.View
          key={i}
          style={[styles.skeletonBlock, { width: `${w}%`, height: 16, marginBottom: 12, marginHorizontal: 16 }, skeletonStyle]}
        />
      ))}
    </View>
  );
}

// ============================================================================
// ShellErrorState (Section 3.28)
// ============================================================================

interface ShellErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ShellErrorState({
  message = "We couldn't load the workspace.",
  onRetry,
}: ShellErrorStateProps) {
  return (
    <View style={styles.shellErrorRoot} accessibilityRole="alert">
      <Text style={styles.shellErrorTitle}>Something went wrong</Text>
      <Text style={styles.shellErrorMessage}>{message}</Text>
      {onRetry && (
        <TouchableOpacity
          style={styles.retryButton}
          onPress={onRetry}
          accessibilityRole="button"
          accessibilityLabel="Try again"
        >
          <Text style={styles.retryButtonText}>Try Again</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

// ============================================================================
// ApplicationShell (Root Composition — Section 3.1 & 3.7)
// ============================================================================

interface ApplicationShellProps {
  children: ReactNode;
  config: ApplicationShellConfig;
  toasts?: Toast[];
  onNavigate?: (route: string) => void;
  onSearchPress?: () => void;
  onNotificationsPress?: () => void;
  onUserMenuPress?: () => void;
  onToastDismiss?: (toastId: string) => void;
  onRetry?: () => void;
}

export function ApplicationShell({
  children,
  config,
  toasts = [],
  onNavigate,
  onSearchPress,
  onNotificationsPress,
  onUserMenuPress,
  onToastDismiss,
  onRetry,
}: ApplicationShellProps) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const { width } = useWindowDimensions();
  const layoutMode = resolveShellLayoutMode(width);

  if (config.loadState === 'loading') {
    return <ShellLoadingState />;
  }

  if (config.loadState === 'error') {
    return <ShellErrorState onRetry={onRetry} />;
  }

  return (
    <View style={styles.shellRoot}>
      <SkipNavigation />

      {/* Global Header (landmark: banner) */}
      <AppHeader
        brandName={config.header.brandName}
        notificationCount={config.header.notificationCount}
        showSearch={config.header.showSearch}
        showNotifications={config.header.showNotifications}
        showUserMenu={config.header.showUserMenu}
        onSearchPress={onSearchPress}
        onNotificationsPress={onNotificationsPress}
        onUserMenuPress={onUserMenuPress}
        onMenuPress={() => setIsDrawerOpen(true)}
        layoutMode={layoutMode}
      />

      {/* Main Layout Region (landmark: main — rendered inside PageContainer) */}
      <View style={styles.shellBody}>
        {children}
      </View>

      {/* Mobile Bottom Navigation (landmark: navigation) */}
      {layoutMode === 'mobile' && (
        <MobileBottomNavigation
          navConfig={config.navigation}
          activeRoute={config.activeRoute}
          onNavigate={(route) => onNavigate?.(route)}
          onMenuPress={() => setIsDrawerOpen(true)}
        />
      )}

      {/* Mobile Navigation Drawer */}
      <MobileNavigationDrawer
        isOpen={isDrawerOpen}
        navConfig={config.navigation}
        activeRoute={config.activeRoute}
        onClose={() => setIsDrawerOpen(false)}
        onNavigate={(route) => onNavigate?.(route)}
      />

      {/* Toast Region */}
      <ToastRegion toasts={toasts} onDismiss={(id) => onToastDismiss?.(id)} />
    </View>
  );
}

// ============================================================================
// Styles (all values from Phase 02 design tokens)
// ============================================================================

const styles = StyleSheet.create({
  // Skip navigation
  skipNav: { position: 'absolute', top: -100, left: 0, right: 0, zIndex: zIndexScale.max, opacity: 0 },
  skipNavText: { fontSize: 14, color: neutralPrimitives.neutral900, backgroundColor: neutralPrimitives.neutral0, padding: 8 },

  // Shell root
  shellRoot: { flex: 1, backgroundColor: lightSemanticSurfaces.primary },
  shellBody: { flex: 1 },

  // App header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacingScale.space4,
    paddingBottom: 12,
    backgroundColor: lightSemanticSurfaces.primary,
    borderBottomWidth: 1,
    borderBottomColor: lightSemanticBorders.subtle,
    zIndex: zIndexScale.sticky,
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  brandName: { fontSize: typeScale.headingS.fontSize, fontWeight: '700', color: lightSemanticContent.primary, letterSpacing: -0.5 },
  headerIconButton: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', borderRadius: radiusScale.full },
  headerIconText: { fontSize: 20 },

  // Search bar
  searchBar: { flexDirection: 'row', alignItems: 'center', borderRadius: radiusScale.sm, backgroundColor: lightSemanticSurfaces.secondary, borderWidth: 1, borderColor: lightSemanticBorders.default },
  searchBarMobile: { width: 40, height: 40, justifyContent: 'center', alignItems: 'center', flex: 0 },
  searchBarDesktop: { flex: 1, marginHorizontal: spacingScale.space4, height: 40, paddingHorizontal: spacingScale.space3 },
  searchIcon: { fontSize: 16 },
  searchPlaceholder: { fontSize: typeScale.bodyS.fontSize, color: lightSemanticContent.tertiary, marginLeft: 8, flex: 1 },

  // Badge
  badge: { position: 'absolute', top: 4, right: 4, width: 16, height: 16, borderRadius: 8, backgroundColor: brandPalette.accent, alignItems: 'center', justifyContent: 'center' },
  badgeText: { fontSize: 9, fontWeight: '700', color: neutralPrimitives.neutral0 },
  avatar: { width: 36, height: 36, borderRadius: radiusScale.full, backgroundColor: lightSemanticSurfaces.tertiary, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: typeScale.labelM.fontSize, fontWeight: '600', color: lightSemanticContent.primary },

  // Bottom navigation
  bottomNav: {
    flexDirection: 'row',
    backgroundColor: lightSemanticSurfaces.primary,
    borderTopWidth: 1,
    borderTopColor: lightSemanticBorders.subtle,
    paddingTop: spacingScale.space2,
    paddingHorizontal: spacingScale.space2,
    zIndex: zIndexScale.sticky,
  },
  bottomNavItem: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingVertical: 4, minHeight: 44 },
  bottomNavIcon: { fontSize: 20, color: lightSemanticContent.tertiary },
  bottomNavIconActive: { color: brandPalette.primary },
  bottomNavLabel: { fontSize: 10, color: lightSemanticContent.tertiary, marginTop: 2 },
  bottomNavLabelActive: { color: brandPalette.primary, fontWeight: '600' },

  // Drawer
  drawerScrim: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)' },
  drawerPanel: { position: 'absolute', top: 0, left: 0, bottom: 0, width: 280, backgroundColor: lightSemanticSurfaces.primary, zIndex: zIndexScale.modal },
  drawerHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: spacingScale.space4, borderBottomWidth: 1, borderBottomColor: lightSemanticBorders.subtle },
  drawerBrand: { fontSize: typeScale.headingM.fontSize, fontWeight: '700', color: lightSemanticContent.primary },
  drawerClose: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  drawerCloseText: { fontSize: 18, color: lightSemanticContent.secondary },
  drawerGroup: { paddingVertical: spacingScale.space2 },
  drawerDivider: { height: 1, backgroundColor: lightSemanticBorders.subtle, marginHorizontal: spacingScale.space4, marginVertical: spacingScale.space2 },
  drawerItem: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacingScale.space4, paddingVertical: 12, minHeight: 44 },
  drawerItemActive: { backgroundColor: lightSemanticSurfaces.secondary },
  drawerItemIcon: { fontSize: 18, width: 28 },
  drawerItemLabel: { fontSize: typeScale.bodyM.fontSize, color: lightSemanticContent.secondary, flex: 1 },
  drawerItemLabelActive: { color: lightSemanticContent.primary, fontWeight: '600' },

  // Page container
  pageContainerScroll: { flex: 1 },
  pageContainer: { flexGrow: 1, paddingVertical: spacingScale.space4 },

  // Page header
  pageHeader: { paddingVertical: spacingScale.space4 },
  breadcrumbs: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacingScale.space2 },
  breadcrumbItem: { fontSize: typeScale.caption.fontSize, color: lightSemanticContent.tertiary },
  breadcrumbCurrent: { color: lightSemanticContent.secondary, fontWeight: '500' },
  breadcrumbSep: { fontSize: typeScale.caption.fontSize, color: lightSemanticContent.tertiary },
  pageHeaderTitleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  pageHeaderTitle: { fontSize: typeScale.headingXl.fontSize, fontWeight: '600', color: lightSemanticContent.primary, letterSpacing: -0.01, flex: 1 },
  pageHeaderTitleEditorial: { fontSize: typeScale.displayM.fontSize, fontWeight: '700', letterSpacing: -0.015 },
  pageHeaderDescription: { marginTop: spacingScale.space2, fontSize: typeScale.bodyM.fontSize, color: lightSemanticContent.secondary, lineHeight: 24 },
  pageHeaderResultCount: { marginTop: spacingScale.space1, fontSize: typeScale.bodyS.fontSize, color: lightSemanticContent.tertiary },
  pageHeaderAction: { backgroundColor: lightSemanticActions.primary, paddingHorizontal: spacingScale.space4, paddingVertical: spacingScale.space2, borderRadius: radiusScale.sm, minHeight: 40, justifyContent: 'center' },
  pageHeaderActionText: { fontSize: typeScale.labelL.fontSize, fontWeight: '600', color: lightSemanticActions.primaryText },

  // Content section
  contentSection: { marginBottom: spacingScale.space8 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacingScale.space3 },
  sectionTitle: { fontSize: typeScale.headingM.fontSize, fontWeight: '600', color: lightSemanticContent.primary },
  sectionDescription: { fontSize: typeScale.bodyS.fontSize, color: lightSemanticContent.secondary, marginBottom: spacingScale.space3 },
  sectionAction: { fontSize: typeScale.labelL.fontSize, color: brandPalette.secondary, fontWeight: '600' },

  // Toast
  toastRegion: { position: 'absolute', bottom: 80, left: spacingScale.space4, right: spacingScale.space4, zIndex: zIndexScale.toast, gap: spacingScale.space2 },
  toast: { flexDirection: 'row', alignItems: 'center', backgroundColor: lightSemanticSurfaces.primary, borderRadius: radiusScale.md, padding: spacingScale.space3, borderLeftWidth: 4, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 4 },
  toastIcon: { fontSize: 16, marginRight: spacingScale.space2, fontWeight: '700' },
  toastMessage: { flex: 1, fontSize: typeScale.bodyS.fontSize, color: lightSemanticContent.primary },
  toastDismiss: { fontSize: 14, color: lightSemanticContent.tertiary, paddingLeft: spacingScale.space2 },

  // Shell loading
  shellLoadingRoot: { flex: 1, backgroundColor: lightSemanticSurfaces.primary },
  headerSkeleton: { flexDirection: 'row', alignItems: 'center', padding: spacingScale.space4, borderBottomWidth: 1, borderBottomColor: lightSemanticBorders.subtle, marginBottom: spacingScale.space4 },
  skeletonBlock: { borderRadius: radiusScale.sm },

  // Shell error
  shellErrorRoot: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacingScale.space8 },
  shellErrorTitle: { fontSize: typeScale.headingM.fontSize, fontWeight: '700', color: lightSemanticContent.primary, marginBottom: spacingScale.space2 },
  shellErrorMessage: { fontSize: typeScale.bodyM.fontSize, color: lightSemanticContent.secondary, textAlign: 'center', lineHeight: 24, marginBottom: spacingScale.space6 },
  retryButton: { backgroundColor: lightSemanticActions.primary, paddingHorizontal: spacingScale.space6, paddingVertical: spacingScale.space3, borderRadius: radiusScale.sm, minHeight: 44, justifyContent: 'center' },
  retryButtonText: { fontSize: typeScale.labelL.fontSize, fontWeight: '600', color: lightSemanticActions.primaryText },
});
