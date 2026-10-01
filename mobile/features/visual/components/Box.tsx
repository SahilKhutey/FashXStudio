/**
 * FashXStudio — Box Primitive (Phase 05 - L1 Primitive)
 *
 * Controlled layout & styling primitive consuming Phase 02 tokens for
 * padding, margin, surface backgrounds, borders, and radii (Section 5.4).
 */

import React from 'react';
import { View, ViewStyle } from 'react-native';
import type { BoxProps } from './types';

export function Box({
  children,
  padding,
  margin,
  backgroundColor,
  borderRadius,
  borderColor,
  borderWidth,
  style,
  testID,
}: BoxProps) {
  const dynamicStyle: ViewStyle = {
    padding: padding as any,
    margin: margin as any,
    backgroundColor,
    borderRadius,
    borderColor,
    borderWidth,
  };

  return (
    <View style={[dynamicStyle, style]} testID={testID}>
      {children}
    </View>
  );
}
