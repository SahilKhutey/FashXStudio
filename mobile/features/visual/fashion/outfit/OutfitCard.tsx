/**
 * FashXStudio — OutfitCard Component (Phase 06 - Fashion Content)
 *
 * Outfit combination component emphasizing constituent piece breakdown
 * (top, bottom, shoes, outerwear) and total ensemble price (Section 6.11 & 6.12).
 */

import React from 'react';
import {
  Image,
  Pressable,
  ScrollView,
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
import { Price } from '../../components/Price';
import type { OutfitItem } from '../types';

export interface OutfitCardProps {
  outfit: OutfitItem;
  onPress?: () => void;
  onPiecePress?: (productId: string) => void;
  testID?: string;
}

export function OutfitCard({
  outfit,
  onPress,
  onPiecePress,
  testID,
}: OutfitCardProps) {
  const { title, imageUri, pieces, totalPrice } = outfit;

  return (
    <View style={[styles.card, elevationShadows[1]]} testID={testID}>
      {/* Main hero image */}
      <Pressable
        onPress={onPress}
        style={styles.heroContainer}
        accessibilityRole="button"
        accessibilityLabel={`Outfit: ${title}`}
      >
        <Image
          source={{ uri: imageUri }}
          style={styles.heroImage}
          resizeMode="cover"
        />
        <View style={styles.titleOverlay}>
          <Text style={styles.title} numberOfLines={1}>
            {title}
          </Text>
          {totalPrice && (
            <Price
              amount={totalPrice.amount}
              currencySymbol={totalPrice.currencySymbol || '₹'}
              size="sm"
            />
          )}
        </View>
      </Pressable>

      {/* Horizontal constituent piece carousel */}
      {pieces.length > 0 && (
        <View style={styles.piecesSection}>
          <Text style={styles.piecesLabel}>Items in this outfit ({pieces.length})</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.piecesList}
          >
            {pieces.map((piece) => (
              <Pressable
                key={`${piece.slot}-${piece.productId}`}
                onPress={() => onPiecePress && onPiecePress(piece.productId)}
                style={styles.pieceChip}
                accessibilityRole="button"
                accessibilityLabel={`${piece.slot}: ${piece.productTitle}`}
              >
                <Image
                  source={{ uri: piece.imageUri }}
                  style={styles.pieceThumb}
                  resizeMode="cover"
                />
                <View style={styles.pieceMeta}>
                  <Text style={styles.pieceSlot}>{piece.slot}</Text>
                  <Text style={styles.pieceTitle} numberOfLines={1}>
                    {piece.productTitle}
                  </Text>
                </View>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      )}
    </View>
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
  heroContainer: {
    width: '100%',
    aspectRatio: 16 / 10,
    position: 'relative',
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  titleOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
    paddingHorizontal: spacingScale.space4,
    paddingVertical: spacingScale.space2,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    color: '#FFF',
    fontSize: typeScale.labelM.fontSize,
    fontWeight: '700',
    flex: 1,
  },
  piecesSection: {
    padding: spacingScale.space3,
    backgroundColor: lightSemanticSurfaces.secondary,
  },
  piecesLabel: {
    fontSize: typeScale.caption.fontSize,
    fontWeight: '600',
    color: lightSemanticContent.secondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: spacingScale.space2,
  },
  piecesList: {
    flexDirection: 'row',
    gap: spacingScale.space2,
  },
  pieceChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: lightSemanticSurfaces.primary,
    borderRadius: radiusScale.sm,
    padding: 4,
    borderWidth: 1,
    borderColor: lightSemanticBorders.subtle,
    maxWidth: 180,
  },
  pieceThumb: {
    width: 36,
    height: 36,
    borderRadius: radiusScale.xs,
  },
  pieceMeta: {
    marginLeft: spacingScale.space2,
    flex: 1,
    paddingRight: 4,
  },
  pieceSlot: {
    fontSize: 9,
    fontWeight: '700',
    textTransform: 'uppercase',
    color: lightSemanticContent.tertiary,
  },
  pieceTitle: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.primary,
    fontWeight: '500',
  },
});
