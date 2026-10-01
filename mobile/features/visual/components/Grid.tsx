/**
 * FashXStudio — Grid Primitive (Phase 05 - L1 Primitive)
 *
 * Responsive multi-column layout primitive implementing the Phase 02 grid tokens
 * and adaptive column calculations (Section 5.7).
 */

import React from 'react';
import {
  StyleSheet,
  useWindowDimensions,
  View,
  ViewStyle,
} from 'react-native';

import { spacingScale } from '../tokens/primitives';
import { calculateAdaptiveColumns } from '../tokens/responsive';
import type { GridProps } from './types';

export function Grid({
  children,
  columns,
  gutter = spacingScale.space4,
  style,
  testID,
}: GridProps) {
  const { width } = useWindowDimensions();

  // If columns are not explicitly provided, calculate adaptively from viewport
  const resolvedCols = columns || calculateAdaptiveColumns(width, 240, gutter);

  const containerStyle: ViewStyle = {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: gutter,
  };

  const itemWidthPercent = `${(100 / resolvedCols) - (gutter * (resolvedCols - 1) / (resolvedCols * width) * 100)}%`;

  return (
    <View style={[styles.base, containerStyle, style]} testID={testID}>
      {React.Children.map(children, (child) => {
        if (!child) return null;
        return (
          <View style={{ flexBasis: `${100 / resolvedCols - 2}%`, flexGrow: 1 }}>
            {child}
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    width: '100%',
  },
});
