/**
 * FashXStudio — IconButton Component (Phase 05 - L2 Core UI)
 *
 * Compact icon action trigger with mandatory accessible name and
 * WCAG 2.2 target size >= 44px (Section 5.13).
 */

import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
} from 'react-native';

import {
  neutralPrimitives,
  radiusScale,
} from '../tokens/primitives';
import { lightSemanticContent } from '../tokens/semantic';
import type { IconButtonProps } from './types';

export function IconButton({
  icon,
  accessibilityLabel,
  onPress,
  size = 'md',
  variant = 'ghost',
  isDisabled = false,
  testID,
}: IconButtonProps) {
  const getContainerSize = () => {
    switch (size) {
      case 'sm':
        return 44; // Enforce 44px minimum for WCAG 2.2 AA
      case 'lg':
        return 56;
      case 'md':
      default:
        return 48;
    }
  };

  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 16;
      case 'lg':
        return 24;
      case 'md':
      default:
        return 20;
    }
  };

  const dimension = getContainerSize();
  const iconSize = getIconSize();

  return (
    <Pressable
      onPress={isDisabled ? undefined : onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.base,
        {
          width: dimension,
          height: dimension,
          backgroundColor: pressed
            ? neutralPrimitives.neutral100
            : 'transparent',
          opacity: isDisabled ? 0.4 : 1,
        },
      ]}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={{ disabled: isDisabled }}
      testID={testID}
    >
      <Text
        style={[
          styles.iconText,
          {
            fontSize: iconSize,
            color: lightSemanticContent.primary,
          },
        ]}
      >
        {icon}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radiusScale.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: {
    textAlign: 'center',
  },
});
