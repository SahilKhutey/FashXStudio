/**
 * FashXStudio — Badge Primitive (Phase 05)
 *
 * Production status badge, filter pill, and dismissible tag component.
 * Supports 8 variants (default, brand, success, warning, error, accent,
 * neutral, outline), pill or rounded radius, sm/md sizing, and dismiss trigger.
 * Consumes Phase 02 status and brand tokens.
 */

import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  brandPalette,
  neutralPrimitives,
  radiusScale,
  spacingScale,
  statusPalette,
  typeScale,
} from '../tokens/primitives';
import type { BadgeProps } from './types';

export function Badge({
  label,
  variant = 'default',
  size = 'md',
  isPill = true,
  isDismissible = false,
  onDismiss,
  icon,
  testID,
}: BadgeProps) {
  const getColors = () => {
    switch (variant) {
      case 'brand':
        return {
          bg: brandPalette.primary,
          text: neutralPrimitives.neutral0,
          border: 'transparent',
        };
      case 'success':
        return {
          bg: '#ECFDF5', // subtle 50
          text: '#065F46', // deep 800 for WCAG AAA
          border: '#A7F3D0',
        };
      case 'warning':
        return {
          bg: '#FFFBEB',
          text: '#92400E',
          border: '#FDE68A',
        };
      case 'error':
        return {
          bg: '#FEF2F2',
          text: '#991B1B',
          border: '#FECACA',
        };
      case 'accent':
        return {
          bg: brandPalette.accent,
          text: neutralPrimitives.neutral0,
          border: 'transparent',
        };
      case 'neutral':
        return {
          bg: neutralPrimitives.neutral100,
          text: neutralPrimitives.neutral800,
          border: 'transparent',
        };
      case 'outline':
        return {
          bg: 'transparent',
          text: neutralPrimitives.neutral900,
          border: neutralPrimitives.neutral300,
        };
      case 'default':
      default:
        return {
          bg: neutralPrimitives.neutral900,
          text: neutralPrimitives.neutral0,
          border: 'transparent',
        };
    }
  };

  const colors = getColors();
  const isSm = size === 'sm';

  return (
    <View
      style={[
        styles.base,
        isSm ? styles.size_sm : styles.size_md,
        {
          backgroundColor: colors.bg,
          borderColor: colors.border,
          borderWidth: colors.border !== 'transparent' ? 1 : 0,
          borderRadius: isPill ? radiusScale.full : radiusScale.sm,
        },
      ]}
      accessibilityRole="text"
      testID={testID}
    >
      {icon && <Text style={[styles.icon, { color: colors.text }]}>{icon}</Text>}

      <Text
        style={[
          isSm ? styles.text_sm : styles.text_md,
          { color: colors.text },
        ]}
        numberOfLines={1}
      >
        {label}
      </Text>

      {isDismissible && onDismiss && (
        <Pressable
          onPress={onDismiss}
          style={styles.dismissButton}
          accessibilityRole="button"
          accessibilityLabel={`Dismiss ${label}`}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Text style={[styles.dismissIcon, { color: colors.text }]}>✕</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
  },
  size_sm: {
    paddingHorizontal: spacingScale.space2,
    paddingVertical: 2,
    minHeight: 20,
  },
  size_md: {
    paddingHorizontal: spacingScale.space3,
    paddingVertical: 4,
    minHeight: 26,
  },
  text_sm: {
    fontSize: typeScale.caption.fontSize,
    lineHeight: typeScale.caption.lineHeight,
    fontWeight: '600',
  },
  text_md: {
    fontSize: typeScale.labelS.fontSize,
    lineHeight: typeScale.labelS.lineHeight,
    fontWeight: '600',
  },
  icon: {
    marginRight: 4,
    fontSize: 12,
  },
  dismissButton: {
    marginLeft: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dismissIcon: {
    fontSize: 10,
    fontWeight: '700',
  },
});
