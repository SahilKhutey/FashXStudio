/**
 * FashXStudio — TrendTimeline Component (Phase 06 - Fashion Content)
 *
 * Visual trajectory timeline displaying trend evolution points over time (Section 6.19).
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  brandPalette,
  neutralPrimitives,
  radiusScale,
  spacingScale,
  typeScale,
} from '../../tokens/primitives';
import { lightSemanticContent } from '../../tokens/semantic';
import type { TrendSignalPoint } from '../types';

export interface TrendTimelineProps {
  timeline: TrendSignalPoint[];
  testID?: string;
}

export function TrendTimeline({ timeline, testID }: TrendTimelineProps) {
  return (
    <View style={styles.container} testID={testID}>
      <View style={styles.line} />
      <View style={styles.pointsRow}>
        {timeline.map((point, index) => (
          <View key={point.timestamp} style={styles.pointContainer}>
            <View
              style={[
                styles.node,
                {
                  transform: [{ scale: 0.8 + point.intensity * 0.4 }],
                  backgroundColor:
                    index === timeline.length - 1
                      ? brandPalette.primary
                      : neutralPrimitives.neutral500,
                },
              ]}
            />
            <Text style={styles.dateText}>{point.timestamp}</Text>
            <Text style={styles.labelText} numberOfLines={1}>
              {point.signalLabel}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: spacingScale.space4,
    width: '100%',
    position: 'relative',
  },
  line: {
    position: 'absolute',
    top: spacingScale.space4 + 6,
    left: 20,
    right: 20,
    height: 2,
    backgroundColor: neutralPrimitives.neutral300,
  },
  pointsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  pointContainer: {
    alignItems: 'center',
    maxWidth: 90,
  },
  node: {
    width: 14,
    height: 14,
    borderRadius: radiusScale.full,
    borderWidth: 2,
    borderColor: '#FFF',
    marginBottom: spacingScale.space2,
  },
  dateText: {
    fontSize: 10,
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
  labelText: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.tertiary,
    textAlign: 'center',
  },
});
