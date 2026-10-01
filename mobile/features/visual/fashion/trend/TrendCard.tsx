/**
 * FashXStudio — TrendCard Component (Phase 06 - Fashion Content)
 *
 * Trend representation displaying momentum indicator, regional adoption,
 * and trend trajectory signals (Section 6.17 & 6.18).
 */

import React from 'react';
import {
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  elevationShadows,
  radiusScale,
  spacingScale,
  statusPalette,
  typeScale,
} from '../../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../../tokens/semantic';
import type { TrendItem, TrendMomentum } from '../types';

export interface TrendCardProps {
  trend: TrendItem;
  onPress?: () => void;
  testID?: string;
}

export function TrendCard({ trend, onPress, testID }: TrendCardProps) {
  const { title, category, imageUri, momentum, regions } = trend;

  const getMomentumColor = (m: TrendMomentum) => {
    switch (m) {
      case 'emerging':
        return '#0284C7'; // Sky 600
      case 'peaking':
        return '#D97706'; // Amber 600
      case 'stable':
        return statusPalette.success;
      case 'declining':
        return statusPalette.error;
    }
  };

  const momentumColor = getMomentumColor(momentum);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        elevationShadows[1],
        pressed && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Trend: ${title}, ${category}, status ${momentum}`}
      testID={testID}
    >
      <View style={styles.mediaContainer}>
        <Image source={{ uri: imageUri }} style={styles.image} resizeMode="cover" />
        <View style={[styles.momentumBadge, { backgroundColor: momentumColor }]}>
          <Text style={styles.momentumText}>{momentum.toUpperCase()}</Text>
        </View>
      </View>

      <View style={styles.details}>
        <Text style={styles.category}>{category}</Text>
        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>

        {regions.length > 0 && (
          <Text style={styles.regionsText} numberOfLines={1}>
            Regions: {regions.join(' • ')}
          </Text>
        )}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: lightSemanticSurfaces.primary,
    borderRadius: radiusScale.md,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: lightSemanticBorders.subtle,
    width: '100%',
  },
  pressed: {
    opacity: 0.95,
  },
  mediaContainer: {
    width: '100%',
    aspectRatio: 16 / 10,
    backgroundColor: lightSemanticSurfaces.secondary,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  momentumBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: radiusScale.xs,
  },
  momentumText: {
    color: '#FFF',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  details: {
    padding: spacingScale.space3,
  },
  category: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.tertiary,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  title: {
    fontSize: typeScale.labelM.fontSize,
    fontWeight: '700',
    color: lightSemanticContent.primary,
    marginTop: 2,
  },
  regionsText: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.secondary,
    marginTop: 4,
  },
});
