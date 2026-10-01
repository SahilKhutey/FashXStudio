/**
 * FashXStudio — Typography Primitive (Phase 05)
 *
 * Strict token-mapped typography component supporting 15 type scale roles
 * (display, heading, body, label, caption, overline).
 * Consumes Phase 02 typeScale and semantic content colors.
 */

import React from 'react';
import { StyleSheet, Text, TextStyle } from 'react-native';

import { typeScale } from '../tokens/primitives';
import { lightSemanticContent } from '../tokens/semantic';
import type { TypographyProps, TypographyRole } from './types';

export function Typography({
  role = 'body_m',
  children,
  color,
  align = 'left',
  maxLines,
  accessibilityRole,
  testID,
}: TypographyProps) {
  const isHeader =
    accessibilityRole === 'header' ||
    role.startsWith('display') ||
    role.startsWith('heading');

  const resolvedRole = role.replace('_', '') as keyof typeof typeScaleMap;
  const tokenStyle = typeScaleMap[resolvedRole] || typeScale.bodyM;

  return (
    <Text
      style={[
        tokenStyle,
        {
          color: color || lightSemanticContent.primary,
          textAlign: align,
        },
      ]}
      numberOfLines={maxLines}
      accessibilityRole={isHeader ? 'header' : 'text'}
      testID={testID}
    >
      {children}
    </Text>
  );
}

const typeScaleMap: Record<string, TextStyle> = {
  displayxl: {
    fontSize: typeScale.displayXl.fontSize,
    lineHeight: typeScale.displayXl.lineHeight,
    fontWeight: '700',
    letterSpacing: -1.2,
  },
  displayl: {
    fontSize: typeScale.displayL.fontSize,
    lineHeight: typeScale.displayL.lineHeight,
    fontWeight: '700',
    letterSpacing: -1.0,
  },
  displaym: {
    fontSize: typeScale.displayM.fontSize,
    lineHeight: typeScale.displayM.lineHeight,
    fontWeight: '700',
    letterSpacing: -0.8,
  },
  headingxl: {
    fontSize: typeScale.headingXl.fontSize,
    lineHeight: typeScale.headingXl.lineHeight,
    fontWeight: '600',
    letterSpacing: -0.5,
  },
  headingl: {
    fontSize: typeScale.headingL.fontSize,
    lineHeight: typeScale.headingL.lineHeight,
    fontWeight: '600',
    letterSpacing: -0.4,
  },
  headingm: {
    fontSize: typeScale.headingM.fontSize,
    lineHeight: typeScale.headingM.lineHeight,
    fontWeight: '600',
    letterSpacing: -0.3,
  },
  headings: {
    fontSize: typeScale.headingS.fontSize,
    lineHeight: typeScale.headingS.lineHeight,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  headingxs: {
    fontSize: typeScale.headingXs.fontSize,
    lineHeight: typeScale.headingXs.lineHeight,
    fontWeight: '600',
    letterSpacing: -0.1,
  },
  bodyl: {
    fontSize: typeScale.bodyL.fontSize,
    lineHeight: typeScale.bodyL.lineHeight,
    fontWeight: '400',
  },
  bodym: {
    fontSize: typeScale.bodyM.fontSize,
    lineHeight: typeScale.bodyM.lineHeight,
    fontWeight: '400',
  },
  bodys: {
    fontSize: typeScale.bodyS.fontSize,
    lineHeight: typeScale.bodyS.lineHeight,
    fontWeight: '400',
  },
  labell: {
    fontSize: typeScale.labelL.fontSize,
    lineHeight: typeScale.labelL.lineHeight,
    fontWeight: '600',
  },
  labelm: {
    fontSize: typeScale.labelM.fontSize,
    lineHeight: typeScale.labelM.lineHeight,
    fontWeight: '600',
  },
  labels: {
    fontSize: typeScale.labelS.fontSize,
    lineHeight: typeScale.labelS.lineHeight,
    fontWeight: '600',
  },
  caption: {
    fontSize: typeScale.caption.fontSize,
    lineHeight: typeScale.caption.lineHeight,
    fontWeight: '400',
  },
  overline: {
    fontSize: typeScale.overline.fontSize,
    lineHeight: typeScale.overline.lineHeight,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1.0,
  },
};
