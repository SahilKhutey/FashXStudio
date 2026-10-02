/**
 * ResponsiveGrid — Fluid responsive grid container (Section 14.8 - 14.10).
 *
 * Computes column count dynamically from available width and minimum card width.
 */

import React, { ReactNode } from 'react';
import { View, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { useResponsive } from '../hooks/useResponsive';

interface ResponsiveGridProps {
  children: ReactNode[];
  minCardWidth?: number;
  gap?: number;
  style?: StyleProp<ViewStyle>;
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  minCardWidth = 280,
  gap: customGap,
  style,
}) => {
  const { width, horizontalPadding, gutter } = useResponsive();
  const gap = customGap !== undefined ? customGap : gutter;

  // Available container width
  const availableWidth = width - horizontalPadding * 2;
  // Dynamic column calculation: max(1, floor((available + gap) / (minCardWidth + gap)))
  const cols = Math.max(1, Math.floor((availableWidth + gap) / (minCardWidth + gap)));
  const itemWidth = Math.floor((availableWidth - (cols - 1) * gap) / cols);

  return (
    <View style={[styles.gridContainer, { gap }, style]}>
      {React.Children.map(children, (child, idx) => (
        <View key={idx} style={{ width: itemWidth }}>
          {child}
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    width: '100%',
  },
});
