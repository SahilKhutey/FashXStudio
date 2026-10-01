/**
 * FashXStudio — BrandCard Component (Phase 06 - Fashion Content)
 *
 * Brand identity showcase card preserving brand visual assets,
 * fashion category, and verified merchant authenticity (Section 6.20 & 6.21).
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
  typeScale,
} from '../../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../../tokens/semantic';
import type { BrandItem } from '../types';

export interface BrandCardProps {
  brand: BrandItem;
  onPress?: () => void;
  testID?: string;
}

export function BrandCard({ brand, onPress, testID }: BrandCardProps) {
  const { name, logoUri, category, productCount, isVerified } = brand;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        elevationShadows[1],
        pressed && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Brand: ${name}, ${category}, ${productCount} items`}
      testID={testID}
    >
      <View style={styles.logoContainer}>
        <Image source={{ uri: logoUri }} style={styles.logo} resizeMode="contain" />
      </View>

      <View style={styles.details}>
        <View style={styles.nameRow}>
          <Text style={styles.name} numberOfLines={1}>
            {name}
          </Text>
          {isVerified && <Text style={styles.verifiedBadge}>✓</Text>}
        </View>

        <Text style={styles.category} numberOfLines={1}>
          {category}
        </Text>
        <Text style={styles.productCount}>{productCount} Products</Text>
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
    padding: spacingScale.space4,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacingScale.space3,
  },
  pressed: {
    opacity: 0.94,
  },
  logoContainer: {
    width: 60,
    height: 60,
    borderRadius: radiusScale.sm,
    backgroundColor: lightSemanticSurfaces.secondary,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 4,
    marginRight: spacingScale.space3,
  },
  logo: {
    width: '100%',
    height: '100%',
  },
  details: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  name: {
    fontSize: typeScale.labelM.fontSize,
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
  verifiedBadge: {
    marginLeft: 6,
    fontSize: 12,
    color: '#0284C7',
    fontWeight: '700',
  },
  category: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.secondary,
    marginTop: 1,
  },
  productCount: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.tertiary,
    marginTop: 2,
    fontWeight: '500',
  },
});
