/**
 * FashXStudio — Alert Component (Phase 05 - L2 Core UI)
 *
 * Persistent inline notification banner for error, warning, success,
 * and informational messages with optional action retry (Section 5.31).
 */

import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  radiusScale,
  spacingScale,
  statusPalette,
  typeScale,
} from '../tokens/primitives';
import { lightSemanticContent } from '../tokens/semantic';
import type { AlertProps } from './types';

export function Alert({
  variant = 'info',
  title,
  message,
  actionLabel,
  onAction,
  isDismissible = false,
  onDismiss,
  testID,
}: AlertProps) {
  const getColors = () => {
    switch (variant) {
      case 'error':
        return {
          bg: '#FEF2F2',
          border: '#FECACA',
          iconColor: statusPalette.error,
          icon: '⚠️',
        };
      case 'warning':
        return {
          bg: '#FFFBEB',
          border: '#FDE68A',
          iconColor: statusPalette.warning,
          icon: '⚡',
        };
      case 'success':
        return {
          bg: '#ECFDF5',
          border: '#A7F3D0',
          iconColor: statusPalette.success,
          icon: '✓',
        };
      case 'info':
      default:
        return {
          bg: '#EFF6FF',
          border: '#BFDBFE',
          iconColor: statusPalette.info,
          icon: 'ℹ',
        };
    }
  };

  const colors = getColors();

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: colors.bg,
          borderColor: colors.border,
        },
      ]}
      accessibilityRole="alert"
      accessibilityLiveRegion="polite"
      testID={testID}
    >
      <Text style={[styles.icon, { color: colors.iconColor }]}>
        {colors.icon}
      </Text>

      <View style={styles.content}>
        {title && <Text style={styles.title}>{title}</Text>}
        <Text style={styles.message}>{message}</Text>

        {actionLabel && onAction && (
          <Pressable
            onPress={onAction}
            style={styles.actionButton}
            accessibilityRole="button"
            accessibilityLabel={actionLabel}
          >
            <Text style={[styles.actionText, { color: colors.iconColor }]}>
              {actionLabel}
            </Text>
          </Pressable>
        )}
      </View>

      {isDismissible && onDismiss && (
        <Pressable
          onPress={onDismiss}
          style={styles.dismissButton}
          accessibilityRole="button"
          accessibilityLabel="Dismiss alert"
        >
          <Text style={styles.dismissIcon}>✕</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    borderWidth: 1,
    borderRadius: radiusScale.md,
    padding: spacingScale.space3,
    marginBottom: spacingScale.space3,
    width: '100%',
  },
  icon: {
    fontSize: 18,
    marginRight: spacingScale.space3,
    marginTop: 1,
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: typeScale.labelM.fontSize,
    fontWeight: '700',
    color: lightSemanticContent.primary,
    marginBottom: 2,
  },
  message: {
    fontSize: typeScale.bodyS.fontSize,
    lineHeight: typeScale.bodyS.lineHeight,
    color: lightSemanticContent.secondary,
  },
  actionButton: {
    marginTop: spacingScale.space2,
    alignSelf: 'flex-start',
    minHeight: 32,
    justifyContent: 'center',
  },
  actionText: {
    fontSize: typeScale.labelS.fontSize,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  dismissButton: {
    padding: 4,
    marginLeft: spacingScale.space2,
  },
  dismissIcon: {
    fontSize: 14,
    color: lightSemanticContent.tertiary,
  },
});
