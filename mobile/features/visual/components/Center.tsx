/**
 * FashXStudio — Center Primitive (Phase 05 - L1 Primitive)
 *
 * Centering layout container utility for icons, loaders, and empty states.
 */

import React from 'react';
import { StyleSheet, View } from 'react-native';
import type { CenterProps } from './types';

export function Center({ children, style, testID }: CenterProps) {
  return (
    <View style={[styles.center, style]} testID={testID}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  center: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
