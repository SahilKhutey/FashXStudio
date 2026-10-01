/**
 * FashXStudio — Skeleton Primitive (Phase 05)
 *
 * Structural placeholder component with animated opacity pulse loop.
 * Supports rectangle, rounded, circle, and text shapes.
 * Consumes Phase 02 neutral color primitives and motion tokens.
 */

import React, { useEffect, useRef } from 'react';
import {
  Animated,
  StyleSheet,
  ViewStyle,
} from 'react-native';

import {
  neutralPrimitives,
  radiusScale,
} from '../tokens/primitives';
import type { SkeletonProps } from './types';

export function Skeleton({
  shape = 'rectangle',
  width = '100%',
  height = 16,
  borderRadius,
  isAnimated = true,
  testID,
}: SkeletonProps) {
  const pulseAnim = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    if (!isAnimated) return;

    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 0.9,
          duration: 750,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0.4,
          duration: 750,
          useNativeDriver: true,
        }),
      ]),
    );

    pulse.start();
    return () => pulse.stop();
  }, [isAnimated, pulseAnim]);

  const getBorderRadius = (): number => {
    if (borderRadius !== undefined) return borderRadius;
    switch (shape) {
      case 'circle':
        return 9999;
      case 'rounded':
        return radiusScale.md;
      case 'text':
        return radiusScale.xs;
      case 'rectangle':
      default:
        return radiusScale.sm;
    }
  };

  const dynamicStyle: ViewStyle = {
    width: width as any,
    height: height as any,
    borderRadius: getBorderRadius(),
    backgroundColor: neutralPrimitives.neutral200,
  };

  return (
    <Animated.View
      style={[
        styles.base,
        dynamicStyle,
        isAnimated && { opacity: pulseAnim },
      ]}
      accessibilityRole="none"
      accessible={false}
      testID={testID}
    />
  );
}

const styles = StyleSheet.create({
  base: {
    overflow: 'hidden',
  },
});
