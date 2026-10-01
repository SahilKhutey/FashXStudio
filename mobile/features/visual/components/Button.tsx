/**
 * FashXStudio — Button Primitive (Phase 05)
 *
 * Production interactive trigger supporting 5 variants (primary, secondary,
 * outline, ghost, destructive), 3 sizes (sm, md, lg), loading spinner,
 * disabled state, and strict WCAG 2.2 AA target size (>= 44px).
 * Consumes Phase 02 design tokens exclusively.
 */

import React from 'react';
import {
  ActivityIndicator,
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
import {
  lightSemanticActions,
  lightSemanticBorders,
  lightSemanticContent,
} from '../tokens/semantic';
import type { ButtonProps } from './types';

export function Button({
  variant = 'primary',
  size = 'md',
  label,
  onPress,
  icon,
  iconPosition = 'left',
  isLoading = false,
  isDisabled = false,
  isFullWidth = false,
  accessibilityLabel,
  testID,
}: ButtonProps) {
  const getContainerStyle = (pressed: boolean) => {
    const baseStyle: any = [
      styles.base,
      styles[`size_${size}`],
      isFullWidth && styles.fullWidth,
    ];

    switch (variant) {
      case 'primary':
        baseStyle.push({
          backgroundColor: isDisabled
            ? neutralPrimitives.neutral300
            : pressed
            ? neutralPrimitives.neutral800
            : lightSemanticActions.primary,
        });
        break;
      case 'secondary':
        baseStyle.push({
          backgroundColor: isDisabled
            ? neutralPrimitives.neutral100
            : pressed
            ? neutralPrimitives.neutral200
            : lightSemanticActions.secondary,
        });
        break;
      case 'outline':
        baseStyle.push({
          backgroundColor: pressed ? neutralPrimitives.neutral100 : 'transparent',
          borderWidth: 1,
          borderColor: isDisabled
            ? lightSemanticBorders.subtle
            : lightSemanticBorders.strong,
        });
        break;
      case 'ghost':
        baseStyle.push({
          backgroundColor: pressed ? neutralPrimitives.neutral100 : 'transparent',
        });
        break;
      case 'destructive':
        baseStyle.push({
          backgroundColor: isDisabled
            ? neutralPrimitives.neutral300
            : pressed
            ? '#DC2626'
            : statusPalette.error,
        });
        break;
    }

    return baseStyle;
  };

  const getTextColor = () => {
    if (isDisabled) return neutralPrimitives.neutral500;
    switch (variant) {
      case 'primary':
      case 'destructive':
        return neutralPrimitives.neutral0;
      case 'secondary':
      case 'outline':
      case 'ghost':
        return lightSemanticContent.primary;
    }
  };

  const textColor = getTextColor();
  const textSizeStyle = styles[`textSize_${size}`];

  return (
    <Pressable
      onPress={isDisabled || isLoading ? undefined : onPress}
      disabled={isDisabled || isLoading}
      style={({ pressed }) => getContainerStyle(pressed)}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || label}
      accessibilityState={{ disabled: isDisabled, busy: isLoading }}
      testID={testID}
    >
      <View style={styles.contentRow}>
        {isLoading ? (
          <ActivityIndicator
            size="small"
            color={textColor}
            style={styles.spinner}
          />
        ) : (
          <>
            {icon && iconPosition === 'left' && (
              <Text style={[styles.icon, { color: textColor }]}>{icon}</Text>
            )}
            <Text
              style={[styles.text, textSizeStyle, { color: textColor }]}
              numberOfLines={1}
            >
              {label}
            </Text>
            {icon && iconPosition === 'right' && (
              <Text style={[styles.iconRight, { color: textColor }]}>{icon}</Text>
            )}
          </>
        )}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radiusScale.sm,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
  },
  fullWidth: {
    width: '100%',
  },
  contentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    fontWeight: '600',
    textAlign: 'center',
  },
  icon: {
    marginRight: spacingScale.space2,
    fontSize: 16,
  },
  iconRight: {
    marginLeft: spacingScale.space2,
    fontSize: 16,
  },
  spinner: {
    marginVertical: 2,
  },
  // WCAG target sizes: all >= 44px minHeight
  size_sm: {
    minHeight: 44,
    paddingHorizontal: spacingScale.space3,
    paddingVertical: spacingScale.space2,
  },
  size_md: {
    minHeight: 48,
    paddingHorizontal: spacingScale.space4,
    paddingVertical: spacingScale.space3,
  },
  size_lg: {
    minHeight: 56,
    paddingHorizontal: spacingScale.space6,
    paddingVertical: spacingScale.space4,
    borderRadius: radiusScale.md,
  },
  textSize_sm: {
    fontSize: typeScale.labelS.fontSize,
    lineHeight: typeScale.labelS.lineHeight,
  },
  textSize_md: {
    fontSize: typeScale.labelM.fontSize,
    lineHeight: typeScale.labelM.lineHeight,
  },
  textSize_lg: {
    fontSize: typeScale.labelL.fontSize,
    lineHeight: typeScale.labelL.lineHeight,
  },
});
