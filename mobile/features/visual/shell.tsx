/**
 * FashXStudio — Application Shell & Layout Architecture Primitives
 * Phase 01: Visual Product Architecture
 */

import React, { ReactNode } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from "react-native";
import { computeBreakpointMetrics } from "./responsive";
import { UiStateEnvelope } from "./types";

interface AppShellProps {
  children: ReactNode;
  headerTitle?: string;
  headerRightAction?: ReactNode;
  onBackPress?: () => void;
  showBack?: boolean;
}

export function AppShell({
  children,
  headerTitle,
  headerRightAction,
  onBackPress,
  showBack = false,
}: AppShellProps) {
  const { width, height } = useWindowDimensions();
  const metrics = computeBreakpointMetrics(width, height);

  return (
    <View style={styles.shellRoot}>
      {headerTitle ? (
        <View style={[styles.topBar, { paddingHorizontal: metrics.margin }]}>
          <View style={styles.topBarLeft}>
            {showBack && onBackPress && (
              <TouchableOpacity
                onPress={onBackPress}
                accessibilityRole="button"
                accessibilityLabel="Go back"
                style={styles.backButton}
              >
                <Text style={styles.backText}>‹</Text>
              </TouchableOpacity>
            )}
            <Text style={styles.headerTitleText} numberOfLines={1}>
              {headerTitle}
            </Text>
          </View>
          {headerRightAction && <View style={styles.topBarRight}>{headerRightAction}</View>}
        </View>
      ) : null}

      <View
        style={[
          styles.mainContent,
          metrics.contentMaxWidth ? { maxWidth: metrics.contentMaxWidth, alignSelf: "center", width: "100%" } : null,
        ]}
      >
        {children}
      </View>
    </View>
  );
}

interface ScreenContainerProps {
  children: ReactNode;
  scrollable?: boolean;
  padded?: boolean;
}

export function ScreenContainer({
  children,
  scrollable = true,
  padded = true,
}: ScreenContainerProps) {
  const { width, height } = useWindowDimensions();
  const metrics = computeBreakpointMetrics(width, height);

  const containerPadding = padded ? { paddingHorizontal: metrics.margin, paddingVertical: 16 } : undefined;

  if (scrollable) {
    return (
      <ScrollView
        style={styles.containerRoot}
        contentContainerStyle={[styles.scrollContent, containerPadding]}
        keyboardShouldPersistTaps="handled"
      >
        {children}
      </ScrollView>
    );
  }

  return <View style={[styles.containerRoot, containerPadding]}>{children}</View>;
}

interface StateBoundaryProps<T> {
  envelope: UiStateEnvelope<T>;
  onRetry?: () => void;
  loadingSkeleton?: ReactNode;
  children: (data: T) => ReactNode;
}

export function StateBoundary<T>({
  envelope,
  onRetry,
  loadingSkeleton,
  children,
}: StateBoundaryProps<T>) {
  if (envelope.state === "loading") {
    if (loadingSkeleton) return <>{loadingSkeleton}</>;
    return (
      <View style={styles.centerState}>
        <ActivityIndicator size="large" color="#0A0A0A" />
        <Text style={styles.stateMessage}>Loading fashion intelligence...</Text>
      </View>
    );
  }

  if (envelope.state === "error") {
    return (
      <View style={styles.centerState}>
        <Text style={styles.errorIcon}>⚠️</Text>
        <Text style={styles.errorTitle}>Something went wrong</Text>
        <Text style={styles.stateMessage}>{envelope.errorMessage || "Unable to display this view."}</Text>
        {envelope.errorTraceId ? (
          <Text style={styles.traceText}>Trace ID: {envelope.errorTraceId}</Text>
        ) : null}
        {envelope.isRetryable && onRetry ? (
          <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        ) : null}
      </View>
    );
  }

  if (envelope.state === "empty") {
    return (
      <View style={styles.centerState}>
        <Text style={styles.emptyIcon}>✨</Text>
        <Text style={styles.emptyTitle}>{envelope.emptyTitle || "No items discovered"}</Text>
        <Text style={styles.stateMessage}>Check back soon or explore trending items.</Text>
      </View>
    );
  }

  if (envelope.state === "offline") {
    return (
      <View style={styles.centerState}>
        <Text style={styles.emptyIcon}>📡</Text>
        <Text style={styles.emptyTitle}>You're Offline</Text>
        <Text style={styles.stateMessage}>{envelope.errorMessage}</Text>
        {onRetry && (
          <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
            <Text style={styles.retryButtonText}>Reconnect</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  if (envelope.data !== null) {
    return <>{children(envelope.data)}</>;
  }

  return null;
}

const styles = StyleSheet.create({
  shellRoot: {
    flex: 1,
    backgroundColor: "#FAFAFA",
  },
  topBar: {
    height: 56,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#FFFFFF",
    borderBottomWidth: 1,
    borderBottomColor: "#E5E5E5",
  },
  topBarLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  topBarRight: {
    flexDirection: "row",
    alignItems: "center",
  },
  backButton: {
    marginRight: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  backText: {
    fontSize: 24,
    color: "#0A0A0A",
    fontWeight: "600",
  },
  headerTitleText: {
    fontSize: 18,
    fontWeight: "700",
    color: "#0A0A0A",
    letterSpacing: -0.2,
  },
  mainContent: {
    flex: 1,
  },
  containerRoot: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  centerState: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
    minHeight: 280,
  },
  stateMessage: {
    marginTop: 12,
    fontSize: 14,
    color: "#737373",
    textAlign: "center",
    lineHeight: 20,
  },
  errorIcon: {
    fontSize: 36,
  },
  errorTitle: {
    marginTop: 12,
    fontSize: 18,
    fontWeight: "700",
    color: "#171717",
  },
  emptyIcon: {
    fontSize: 36,
  },
  emptyTitle: {
    marginTop: 12,
    fontSize: 18,
    fontWeight: "700",
    color: "#171717",
  },
  traceText: {
    marginTop: 8,
    fontSize: 11,
    fontFamily: "monospace",
    color: "#A3A3A3",
  },
  retryButton: {
    marginTop: 20,
    backgroundColor: "#0A0A0A",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
});
