/**
 * ResponsiveContainer — Max-width bounded content container (Section 14.5 - 14.7).
 *
 * Enforces horizontal padding, max-width constraints, and centering on ultra-wide screens.
 */

import React, { ReactNode } from 'react';
import { View, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { useResponsive } from '../hooks/useResponsive';

interface ResponsiveContainerProps {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
  fullWidth?: boolean;
}

export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  style,
  fullWidth = false,
}) => {
  const { containerMaxWidth, horizontalPadding } = useResponsive();

  return (
    <View style={styles.outerWrapper}>
      <View
        style={[
          styles.innerContainer,
          {
            paddingHorizontal: horizontalPadding,
            maxWidth: fullWidth ? '100%' : containerMaxWidth,
          },
          style,
        ]}
      >
        {children}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  outerWrapper: {
    width: '100%',
    alignItems: 'center',
  },
  innerContainer: {
    width: '100%',
  },
});
