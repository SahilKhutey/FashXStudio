/**
 * FashXStudio — Card Component (Phase 05 - Level 2 Core UI)
 *
 * Versatile container surface supporting 3 variants (elevated, outlined, filled),
 * 0-5 elevation levels, 4 padding scales, and optional pressable feedback.
 * Consumes Phase 02 elevation shadows, surface, and border tokens.
 */

import React from 'react';
import {
  Pressable,
  StyleSheet,
  View,
  ViewStyle,
} from 'react-native';

import {
  elevationShadows,
  radiusScale,
  spacingScale,
} from '../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { CardProps } from './types';

export function Card({
  children,
  variant = 'elevated',
  elevation = 1,
  padding = 'md',
  isClickable = false,
  isHoverable = true,
  onPress,
  accessibilityLabel,
  testID,
}: CardProps) {
  const getPadding = () => {
    switch (padding) {
      case 'none':
        return 0;
      case 'sm':
        return spacingScale.space2;
      case 'lg':
        return spacingScale.space6;
      case 'md':
      default:
        return spacingScale.space4;
    }
  };

  const getContainerStyle = (pressed?: boolean): ViewStyle[] => {
    const base: ViewStyle[] = [
      styles.base,
      { padding: getPadding() },
    ];

    if (variant === 'elevated') {
      base.push({
        backgroundColor: lightSemanticSurfaces.primary,
        ...(elevationShadows[elevation] || elevationShadows[1]),
      });
    } else if (variant === 'outlined') {
      base.push({
        backgroundColor: lightSemanticSurfaces.primary,
        borderWidth: 1,
        borderColor: lightSemanticBorders.default,
      });
    } else if (variant === 'filled') {
      base.push({
        backgroundColor: lightSemanticSurfaces.secondary,
      });
    }

    if (pressed && isClickable) {
      base.push(styles.pressed);
    }

    return base;
  };

  if (isClickable && onPress) {
    return (
      <Pressable
        onPress={onPress}
        style={({ pressed }) => getContainerStyle(pressed)}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        testID={testID}
      >
        {children}
      </Pressable>
    );
  }

  return (
    <View style={getContainerStyle()} testID={testID}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radiusScale.md,
    overflow: 'hidden',
  },
  pressed: {
    opacity: 0.92,
    transform: [{ scale: 0.995 }],
  },
});
