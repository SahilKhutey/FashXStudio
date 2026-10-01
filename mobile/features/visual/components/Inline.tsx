/**
 * FashXStudio — Inline Primitive (Phase 05 - L1 Primitive)
 *
 * Horizontal linear layout primitive supporting gap tokens, alignment,
 * wrapping, and justification (Section 5.6).
 * Used for action rows, tag clusters, metadata, and filter bars.
 */

import React from 'react';
import { View, ViewStyle } from 'react-native';
import { spacingScale } from '../tokens/primitives';
import type { InlineProps } from './types';

export function Inline({
  children,
  gap = spacingScale.space2,
  align = 'center',
  justify = 'flex-start',
  wrap = true,
  style,
  testID,
}: InlineProps) {
  const containerStyle: ViewStyle = {
    flexDirection: 'row',
    alignItems: align,
    justifyContent: justify,
    flexWrap: wrap ? 'wrap' : 'nowrap',
    gap,
  };

  return (
    <View style={[containerStyle, style]} testID={testID}>
      {children}
    </View>
  );
}
