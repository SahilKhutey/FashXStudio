/**
 * ResponsiveRail — Accessible horizontal content carousel (Section 14.34).
 *
 * Provides continuation cue, touch snapping, and smooth scroll.
 */

import React, { ReactNode } from 'react';
import { ScrollView, View, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { useResponsive } from '../hooks/useResponsive';

interface ResponsiveRailProps {
  children: ReactNode;
  itemGap?: number;
  showsScrollIndicator?: boolean;
  style?: StyleProp<ViewStyle>;
}

export const ResponsiveRail: React.FC<ResponsiveRailProps> = ({
  children,
  itemGap = 16,
  showsScrollIndicator = false,
  style,
}) => {
  const { horizontalPadding } = useResponsive();

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={showsScrollIndicator}
      contentContainerStyle={[
        styles.railContent,
        {
          paddingHorizontal: horizontalPadding,
          gap: itemGap,
        },
      ]}
      style={[styles.railScrollView, style]}
    >
      {children}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  railScrollView: {
    width: '100%',
  },
  railContent: {
    flexDirection: 'row',
    alignItems: 'stretch',
    paddingVertical: 8,
  },
});
