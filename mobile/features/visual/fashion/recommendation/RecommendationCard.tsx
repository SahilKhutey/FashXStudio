/**
 * FashXStudio — RecommendationCard Component (Phase 06 - Fashion Content)
 *
 * AI recommendation component displaying target product, confidence badge,
 * and transparent explainability reason chip ("Why this appears") (Section 6.31 & 6.32).
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
  brandPalette,
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
import { Price } from '../../components/Price';
import type { RecommendationItem } from '../types';

export interface RecommendationCardProps {
  recommendation: RecommendationItem;
  onPress?: () => void;
  testID?: string;
}

export function RecommendationCard({
  recommendation,
  onPress,
  testID,
}: RecommendationCardProps) {
  const { product, recommendationLabel, explanationReason, confidenceScore } =
    recommendation;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        elevationShadows[1],
        pressed && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Recommendation: ${product.title}. Reason: ${explanationReason}`}
      testID={testID}
    >
      {/* Explainability Banner */}
      <View style={styles.banner}>
        <Text style={styles.bannerLabel}>{recommendationLabel}</Text>
        <Text style={styles.confidence}>
          {Math.round(confidenceScore * 100)}% match
        </Text>
      </View>

      <View style={styles.mainRow}>
        <Image
          source={{ uri: product.primaryImageUri }}
          style={styles.image}
          resizeMode="cover"
        />

        <View style={styles.details}>
          <Text style={styles.brand} numberOfLines={1}>
            {product.brand}
          </Text>
          <Text style={styles.title} numberOfLines={1}>
            {product.title}
          </Text>

          <View style={styles.priceRow}>
            <Price
              amount={product.price.amount}
              originalAmount={product.price.originalAmount}
              currencySymbol={product.price.currencySymbol}
              discountPercentage={product.price.discountPercentage}
              size="sm"
            />
          </View>
        </View>
      </View>

      {/* Transparent AI explanation */}
      <View style={styles.reasonBox}>
        <Text style={styles.reasonIcon}>✦</Text>
        <Text style={styles.reasonText}>{explanationReason}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: lightSemanticSurfaces.primary,
    borderRadius: radiusScale.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: lightSemanticBorders.subtle,
    width: '100%',
    marginBottom: spacingScale.space4,
  },
  pressed: {
    opacity: 0.95,
  },
  banner: {
    backgroundColor: '#F5F3FF', // Subtle Indigo tint
    paddingHorizontal: spacingScale.space3,
    paddingVertical: 6,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#EDE9FE',
  },
  bannerLabel: {
    fontSize: typeScale.caption.fontSize,
    fontWeight: '700',
    color: brandPalette.secondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  confidence: {
    fontSize: 10,
    fontWeight: '700',
    color: brandPalette.secondary,
  },
  mainRow: {
    flexDirection: 'row',
    padding: spacingScale.space3,
  },
  image: {
    width: 80,
    height: 100,
    borderRadius: radiusScale.sm,
    backgroundColor: lightSemanticSurfaces.secondary,
  },
  details: {
    flex: 1,
    marginLeft: spacingScale.space3,
    justifyContent: 'center',
  },
  brand: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.tertiary,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  title: {
    fontSize: typeScale.labelM.fontSize,
    fontWeight: '600',
    color: lightSemanticContent.primary,
    marginTop: 2,
  },
  priceRow: {
    marginTop: spacingScale.space2,
  },
  reasonBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: lightSemanticSurfaces.secondary,
    paddingHorizontal: spacingScale.space3,
    paddingVertical: spacingScale.space2,
    borderTopWidth: 1,
    borderTopColor: lightSemanticBorders.subtle,
  },
  reasonIcon: {
    color: brandPalette.secondary,
    fontSize: 12,
    marginRight: 6,
    marginTop: 1,
  },
  reasonText: {
    fontSize: typeScale.caption.fontSize,
    lineHeight: typeScale.caption.lineHeight,
    color: lightSemanticContent.secondary,
    flex: 1,
  },
});
