/**
 * ScreenStateWrapper — Master layout lifecycle renderer (Section 15.59 - 15.67).
 *
 * Deterministically renders loading skeletons, empty views, error recovery views,
 * partial degradation banners, or loaded content based on ScreenLifecycleState.
 */

import React, { ReactNode } from 'react';
import {
  View,
  Text,
  ActivityIndicator,
  TouchableOpacity,
  StyleSheet,
  StyleProp,
  ViewStyle,
} from 'react-native';
import { ScreenLifecycleState } from '../types';

interface ScreenStateWrapperProps {
  state: ScreenLifecycleState;
  children: ReactNode;
  emptyHeading?: string;
  emptyDescription?: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
  errorHeading?: string;
  errorDescription?: string;
  onRetry?: () => void;
  partialWarning?: string;
  isOffline?: boolean;
  style?: StyleProp<ViewStyle>;
}

export const ScreenStateWrapper: React.FC<ScreenStateWrapperProps> = ({
  state,
  children,
  emptyHeading = 'No items found',
  emptyDescription = 'There is currently no content available in this section.',
  emptyActionLabel,
  onEmptyAction,
  errorHeading = 'Unable to load content',
  errorDescription = 'A temporary error occurred while retrieving data.',
  onRetry,
  partialWarning,
  isOffline = false,
  style,
}) => {
  // 1. Loading State (Section 15.60 & 15.63)
  if (state === 'loading') {
    return (
      <View style={[styles.centerContainer, style]}>
        <ActivityIndicator size="large" color="#111827" />
        <Text style={styles.loadingText}>Loading content...</Text>
      </View>
    );
  }

  // 2. Empty State (Section 15.64)
  if (state === 'empty') {
    return (
      <View style={[styles.centerContainer, style]}>
        <Text style={styles.emptyIcon}>✦</Text>
        <Text style={styles.emptyHeading}>{emptyHeading}</Text>
        <Text style={styles.emptyDescription}>{emptyDescription}</Text>
        {emptyActionLabel && onEmptyAction && (
          <TouchableOpacity
            onPress={onEmptyAction}
            style={styles.actionButton}
            accessibilityRole="button"
            accessibilityLabel={emptyActionLabel}
          >
            <Text style={styles.actionText}>{emptyActionLabel}</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  // 3. Error State (Section 15.65 & 15.99)
  if (state === 'error') {
    return (
      <View style={[styles.centerContainer, style]}>
        <Text style={styles.errorIcon}>⚠</Text>
        <Text style={styles.errorHeading}>{errorHeading}</Text>
        <Text style={styles.errorDescription}>{errorDescription}</Text>
        {onRetry && (
          <TouchableOpacity
            onPress={onRetry}
            style={styles.retryButton}
            accessibilityRole="button"
            accessibilityLabel="Retry loading content"
          >
            <Text style={styles.retryText}>Try Again</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  // 4. Partial State or Offline Loaded (Section 15.65 & 15.66)
  return (
    <View style={[styles.fullWidth, style]}>
      {isOffline && (
        <View style={styles.offlineBanner} accessibilityLiveRegion="polite">
          <Text style={styles.offlineText}>
            ⚡ Offline mode: Viewing cached items. Live sync paused.
          </Text>
        </View>
      )}

      {state === 'partial' && partialWarning && (
        <View style={styles.partialBanner} accessibilityLiveRegion="polite">
          <Text style={styles.partialText}>⚠ {partialWarning}</Text>
        </View>
      )}

      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  fullWidth: {
    width: '100%',
  },
  centerContainer: {
    width: '100%',
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 280,
  },
  loadingText: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 12,
  },
  emptyIcon: {
    fontSize: 36,
    color: '#9CA3AF',
    marginBottom: 12,
  },
  emptyHeading: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    textAlign: 'center',
  },
  emptyDescription: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    maxWidth: 320,
    lineHeight: 20,
  },
  actionButton: {
    backgroundColor: '#111827',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 20,
    minHeight: 44, // WCAG touch target
    justifyContent: 'center',
  },
  actionText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  errorIcon: {
    fontSize: 36,
    color: '#DC2626',
    marginBottom: 12,
  },
  errorHeading: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    textAlign: 'center',
  },
  errorDescription: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    maxWidth: 340,
    lineHeight: 20,
  },
  retryButton: {
    backgroundColor: '#DC2626',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 20,
    minHeight: 44,
    justifyContent: 'center',
  },
  retryText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  offlineBanner: {
    backgroundColor: '#374151',
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  offlineText: {
    color: '#F9FAFB',
    fontSize: 12,
    fontWeight: '600',
  },
  partialBanner: {
    backgroundColor: '#FEF3C7',
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#FDE68A',
  },
  partialText: {
    color: '#92400E',
    fontSize: 12,
    fontWeight: '600',
  },
});
