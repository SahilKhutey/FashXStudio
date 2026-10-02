/**
 * ResponsiveStickyAction — Fixed bottom action bar (Section 14.13 & 14.14).
 *
 * Provides safe-area aware sticky purchase and action buttons for mobile experiences.
 */

import React, { ReactNode } from 'react';
import { View, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { useResponsive } from '../hooks/useResponsive';

interface ResponsiveStickyActionProps {
  children: ReactNode;
  safeBottomInset?: number;
  style?: StyleProp<ViewStyle>;
}

export const ResponsiveStickyAction: React.FC<ResponsiveStickyActionProps> = ({
  children,
  safeBottomInset = 16,
  style,
}) => {
  const { isCompact, horizontalPadding } = useResponsive();

  // On desktop/expanded, sticky action bars are not pinned to bottom unless specified
  if (!isCompact) {
    return (
      <View style={[styles.inlineContainer, { paddingHorizontal: horizontalPadding }, style]}>
        {children}
      </View>
    );
  }

  return (
    <View
      style={[
        styles.stickyContainer,
        {
          paddingHorizontal: horizontalPadding,
          paddingBottom: Math.max(16, safeBottomInset),
        },
        style,
      ]}
    >
      <View style={styles.actionsInner}>{children}</View>
    </View>
  );
};

const styles = StyleSheet.create({
  inlineContainer: {
    width: '100%',
    paddingVertical: 16,
  },
  stickyContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    paddingTop: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 8,
  },
  actionsInner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    width: '100%',
  },
});
