/**
 * FeedbackToast — Accessible non-blocking toast notification (Section 15.68 - 15.70).
 *
 * Automatically dismisses after timeout, supports action trigger, and announces to screen readers.
 */

import React, { useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  AccessibilityInfo,
} from 'react-native';

interface FeedbackToastProps {
  visible: boolean;
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  onDismiss: () => void;
  autoDismissMs?: number;
}

export const FeedbackToast: React.FC<FeedbackToastProps> = ({
  visible,
  title,
  message,
  actionLabel,
  onAction,
  onDismiss,
  autoDismissMs = 3000,
}) => {
  useEffect(() => {
    if (visible) {
      // Screen reader announcement (Section 15.15 & 15.79)
      AccessibilityInfo.announceForAccessibility(`${title}: ${message}`);

      if (autoDismissMs) {
        const timer = setTimeout(() => {
          onDismiss();
        }, autoDismissMs);
        return () => clearTimeout(timer);
      }
    }
  }, [visible, title, message, autoDismissMs, onDismiss]);

  if (!visible) return null;

  return (
    <View style={styles.toastContainer} accessibilityLiveRegion="polite">
      <View style={styles.textColumn}>
        <Text style={styles.titleText}>{title}</Text>
        <Text style={styles.messageText}>{message}</Text>
      </View>

      {actionLabel && onAction && (
        <TouchableOpacity
          onPress={onAction}
          style={styles.actionButton}
          accessibilityRole="button"
          accessibilityLabel={actionLabel}
        >
          <Text style={styles.actionText}>{actionLabel}</Text>
        </TouchableOpacity>
      )}

      <TouchableOpacity
        onPress={onDismiss}
        style={styles.closeButton}
        accessibilityRole="button"
        accessibilityLabel="Dismiss notice"
      >
        <Text style={styles.closeText}>✕</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  toastContainer: {
    position: 'absolute',
    bottom: 24,
    left: 20,
    right: 20,
    backgroundColor: '#1F2937',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
    zIndex: 9999,
  },
  textColumn: {
    flex: 1,
    paddingRight: 12,
  },
  titleText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  messageText: {
    color: '#D1D5DB',
    fontSize: 12,
    marginTop: 2,
  },
  actionButton: {
    backgroundColor: '#374151',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    minHeight: 44, // WCAG touch target
    justifyContent: 'center',
    marginRight: 8,
  },
  actionText: {
    color: '#60A5FA',
    fontSize: 13,
    fontWeight: '700',
  },
  closeButton: {
    minWidth: 44,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: {
    color: '#9CA3AF',
    fontSize: 14,
    fontWeight: '600',
  },
});
