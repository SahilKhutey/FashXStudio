/**
 * ResponsiveSplit — Two-column split layout with responsive stacking (Section 14.12 & 14.89).
 *
 * Renders side-by-side on expanded/adaptive viewports and stacked vertically on compact.
 */

import React, { ReactNode } from 'react';
import { View, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { useResponsive } from '../hooks/useResponsive';

interface ResponsiveSplitProps {
  primary: ReactNode;
  secondary: ReactNode;
  primaryRatio?: number; // e.g. 0.6 for 60%
  gap?: number;
  reverseOnMobile?: boolean;
  style?: StyleProp<ViewStyle>;
}

export const ResponsiveSplit: React.FC<ResponsiveSplitProps> = ({
  primary,
  secondary,
  primaryRatio = 0.55,
  gap = 24,
  reverseOnMobile = false,
  style,
}) => {
  const { isCompact } = useResponsive();

  if (isCompact) {
    return (
      <View
        style={[
          styles.stackedContainer,
          {
            flexDirection: reverseOnMobile ? 'column-reverse' : 'column',
            gap,
          },
          style,
        ]}
      >
        <View style={styles.fullWidth}>{primary}</View>
        <View style={styles.fullWidth}>{secondary}</View>
      </View>
    );
  }

  const secondaryRatio = 1 - primaryRatio;

  return (
    <View style={[styles.splitHorizontal, { gap }, style]}>
      <View style={{ flex: primaryRatio }}>{primary}</View>
      <View style={{ flex: secondaryRatio }}>{secondary}</View>
    </View>
  );
};

const styles = StyleSheet.create({
  stackedContainer: {
    width: '100%',
  },
  splitHorizontal: {
    flexDirection: 'row',
    width: '100%',
    alignItems: 'flex-start',
  },
  fullWidth: {
    width: '100%',
  },
});
