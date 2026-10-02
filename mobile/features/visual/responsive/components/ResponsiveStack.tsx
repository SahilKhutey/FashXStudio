/**
 * ResponsiveStack — Responsive linear layout container (Section 14.89).
 *
 * Switches flex direction between column (compact) and row (expanded/adaptive).
 */

import React, { ReactNode } from 'react';
import { View, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { useResponsive } from '../hooks/useResponsive';
import { LayoutMode } from '../types';

interface ResponsiveStackProps {
  children: ReactNode;
  direction?: 'auto' | 'row' | 'column';
  breakpointSwitch?: LayoutMode;
  spacing?: number;
  alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch';
  justifyContent?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around';
  style?: StyleProp<ViewStyle>;
}

export const ResponsiveStack: React.FC<ResponsiveStackProps> = ({
  children,
  direction = 'auto',
  breakpointSwitch = 'compact',
  spacing = 16,
  alignItems = 'stretch',
  justifyContent = 'flex-start',
  style,
}) => {
  const { layoutMode } = useResponsive();

  let flexDir: 'row' | 'column' = 'column';
  if (direction !== 'auto') {
    flexDir = direction;
  } else {
    // If layout mode is compact, stack vertically; otherwise arrange horizontally
    flexDir = layoutMode === breakpointSwitch ? 'column' : 'row';
  }

  return (
    <View
      style={[
        {
          flexDirection: flexDir,
          gap: spacing,
          alignItems,
          justifyContent,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
};
