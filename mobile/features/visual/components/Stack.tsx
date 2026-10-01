/**
 * FashXStudio — Stack Primitive (Phase 05 - L1 Primitive)
 *
 * Vertical linear layout primitive with token-based gaps (Section 5.5).
 * Used across forms, page sections, cards, and content blocks.
 */

import React from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import { spacingScale } from '../tokens/primitives';
import type { StackProps } from './types';

export function Stack({
  children,
  gap = spacingScale.space4,
  align = 'stretch',
  reversed = false,
  style,
  testID,
}: StackProps) {
  const containerStyle: ViewStyle = {
    flexDirection: reversed ? 'column-reverse' : 'column',
    alignItems: align,
    gap,
  };

  return (
    <View style={[styles.base, containerStyle, style]} testID={testID}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    width: '100%',
  },
});
