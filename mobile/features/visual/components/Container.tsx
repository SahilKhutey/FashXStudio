/**
 * FashXStudio — Container Primitive (Phase 05 - L1 Primitive)
 *
 * Content width bounding container enforcing max-width, responsive gutters,
 * and centering across viewports (Section 5.8).
 */

import React from 'react';
import {
  StyleSheet,
  useWindowDimensions,
  View,
  ViewStyle,
} from 'react-native';

import { spacingScale } from '../tokens/primitives';
import type { ContainerProps } from './types';

export function Container({
  children,
  maxWidth = 1280,
  paddingHorizontal,
  centered = true,
  style,
  testID,
}: ContainerProps) {
  const { width } = useWindowDimensions();

  // Responsive gutters: mobile = 16, tablet = 24, desktop = 32
  const defaultGutter =
    width >= 1024
      ? spacingScale.space8
      : width >= 768
      ? spacingScale.space6
      : spacingScale.space4;

  const resolvedPadding =
    paddingHorizontal !== undefined ? paddingHorizontal : defaultGutter;

  const containerStyle: ViewStyle = {
    maxWidth,
    width: '100%',
    paddingHorizontal: resolvedPadding,
    alignSelf: centered ? 'center' : 'flex-start',
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
