/**
 * FashXStudio — Icon Primitive (Phase 05)
 *
 * Consistent icon wrapper with standard sizing (sm=16, md=20, lg=24, xl=32)
 * and semantic color token binding.
 */

import React from 'react';
import { StyleSheet, Text, TextStyle, View } from 'react-native';

import { lightSemanticContent } from '../tokens/semantic';
import type { ComponentSize } from './types';

export interface IconProps {
  name: string;
  size?: ComponentSize | 'xl';
  color?: string;
  accessibilityLabel?: string;
  testID?: string;
}

const sizeMap: Record<string, number> = {
  sm: 16,
  md: 20,
  lg: 24,
  xl: 32,
};

export function Icon({
  name,
  size = 'md',
  color = lightSemanticContent.primary,
  accessibilityLabel,
  testID,
}: IconProps) {
  const pixelSize = sizeMap[size] || 20;

  return (
    <View
      style={[styles.container, { width: pixelSize, height: pixelSize }]}
      accessibilityRole="image"
      accessibilityLabel={accessibilityLabel || name}
      testID={testID}
    >
      <Text
        style={[
          styles.glyph,
          {
            fontSize: pixelSize,
            lineHeight: pixelSize,
            color,
          },
        ]}
      >
        {name}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  glyph: {
    textAlign: 'center',
  },
});
