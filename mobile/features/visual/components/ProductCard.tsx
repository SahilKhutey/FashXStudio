/**
 * FashXStudio — ProductCard Component (Phase 05 - L3 Composite)
 *
 * First major commerce composite component integrating image media,
 * brand, title, price, rating, and wishlist save toggle (Section 5.51).
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
} from '../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import { Price } from './Price';
import { Rating } from './Rating';
import type { ProductCardProps } from './types';

export function ProductCard({
  productId,
  title,
  brand,
  imageUri,
  price,
  originalPrice,
  currencySymbol = '₹',
  rating,
  isSaved = false,
  onPress,
  onSaveToggle,
  badge,
  testID,
}: ProductCardProps) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        elevationShadows[1],
        pressed && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`${title} by ${brand}, ${currencySymbol}${price}`}
      testID={testID}
    >
      {/* Media container */}
      <View style={styles.mediaContainer}>
        <Image
          source={{ uri: imageUri }}
          style={styles.image}
          resizeMode="cover"
        />

        {badge && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{badge}</Text>
          </View>
        )}

        {onSaveToggle && (
          <Pressable
            onPress={onSaveToggle}
            style={styles.saveButton}
            accessibilityRole="button"
            accessibilityLabel={isSaved ? 'Remove from wishlist' : 'Save to wishlist'}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={[styles.saveIcon, isSaved && styles.saveIconActive]}>
              {isSaved ? '❤️' : '🤍'}
            </Text>
          </Pressable>
        )}
      </View>

      {/* Content details */}
      <View style={styles.details}>
        <Text style={styles.brand} numberOfLines={1}>
          {brand}
        </Text>
        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>

        <View style={styles.priceRow}>
          <Price
            amount={price}
            originalAmount={originalPrice}
            currencySymbol={currencySymbol}
            size="sm"
          />
        </View>

        {rating !== undefined && (
          <View style={styles.ratingRow}>
            <Rating value={rating} size="sm" isReadOnly />
          </View>
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
    opacity: 0.94,
    transform: [{ scale: 0.99 }],
  },
  mediaContainer: {
    width: '100%',
    aspectRatio: 3 / 4,
    backgroundColor: lightSemanticSurfaces.secondary,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  badge: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: brandPalette.accent,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: radiusScale.xs,
  },
  badgeText: {
    color: '#FFF',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  saveButton: {
    position: 'absolute',
    top: 6,
    right: 6,
    width: 36,
    height: 36,
    borderRadius: radiusScale.full,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveIcon: {
    fontSize: 16,
  },
  saveIconActive: {
    color: '#EF4444',
  },
  details: {
    padding: spacingScale.space3,
  },
  brand: {
    fontSize: typeScale.caption.fontSize,
    lineHeight: typeScale.caption.lineHeight,
    color: lightSemanticContent.tertiary,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  title: {
    fontSize: typeScale.labelM.fontSize,
    lineHeight: typeScale.labelM.lineHeight,
    fontWeight: '600',
    color: lightSemanticContent.primary,
    marginTop: 2,
  },
  priceRow: {
    marginTop: spacingScale.space2,
  },
  ratingRow: {
    marginTop: spacingScale.space1,
  },
});
