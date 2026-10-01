/**
 * FashXStudio — Divider Primitive (Phase 05)
 *
 * Horizontal or vertical structural divider with subtle, strong,
 * and labeled variants. Consumes Phase 02 border tokens.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  neutralPrimitives,
  spacingScale,
  typeScale,
} from '../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
} from '../tokens/semantic';

export interface DividerProps {
  orientation?: 'horizontal' | 'vertical';
  variant?: 'subtle' | 'strong';
  label?: string;
  testID?: string;
}

export function Divider({
  orientation = 'horizontal',
  variant = 'subtle',
  label,
  testID,
}: DividerProps) {
  const isHorizontal = orientation === 'horizontal';
  const lineColor =
    variant === 'strong'
      ? lightSemanticBorders.strong
      : lightSemanticBorders.subtle;

  if (isHorizontal && label) {
    return (
      <View style={styles.labeledContainer} testID={testID}>
        <View style={[styles.line, { backgroundColor: lineColor }]} />
        <Text style={styles.label}>{label}</Text>
        <View style={[styles.line, { backgroundColor: lineColor }]} />
      </View>
    );
  }

  if (isHorizontal) {
    return (
      <View
        style={[
          styles.horizontalLine,
          { backgroundColor: lineColor },
        ]}
        testID={testID}
      />
    );
  }

  return (
    <View
      style={[
        styles.verticalLine,
        { backgroundColor: lineColor },
      ]}
      testID={testID}
    />
  );
}

const styles = StyleSheet.create({
  horizontalLine: {
    height: 1,
    width: '100%',
    marginVertical: spacingScale.space3,
  },
  verticalLine: {
    width: 1,
    height: '100%',
    marginHorizontal: spacingScale.space3,
  },
  labeledContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: spacingScale.space3,
    width: '100%',
  },
  line: {
    flex: 1,
    height: 1,
  },
  label: {
    paddingHorizontal: spacingScale.space3,
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.tertiary,
    fontWeight: '500',
    textTransform: 'uppercase',
  },
});
