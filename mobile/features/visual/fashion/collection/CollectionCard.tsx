/**
 * FashXStudio — CollectionCard Component (Phase 06 - Fashion Content)
 *
 * Seasonal and thematic collection showcase card with item tally,
 * season tag, and exploration CTA (Section 6.13 & 6.14).
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
import type { CollectionItem } from '../types';

export interface CollectionCardProps {
  collection: CollectionItem;
  onPress?: () => void;
  testID?: string;
}

export function CollectionCard({
  collection,
  onPress,
  testID,
}: CollectionCardProps) {
  const { title, description, heroImageUri, itemCount, seasonTag } = collection;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        elevationShadows[2],
        pressed && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Collection: ${title}, ${itemCount} items`}
      testID={testID}
    >
      <View style={styles.heroContainer}>
        <Image
          source={{ uri: heroImageUri }}
          style={styles.heroImage}
          resizeMode="cover"
        />
        {seasonTag && (
          <View style={styles.seasonBadge}>
            <Text style={styles.seasonText}>{seasonTag}</Text>
          </View>
        )}
      </View>

      <View style={styles.details}>
        <View style={styles.headerRow}>
          <Text style={styles.title} numberOfLines={1}>
            {title}
          </Text>
          <Text style={styles.countBadge}>{itemCount} items</Text>
        </View>

        <Text style={styles.description} numberOfLines={2}>
          {description}
        </Text>

        <Text style={styles.cta}>Explore Collection →</Text>
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
  heroContainer: {
    width: '100%',
    aspectRatio: 16 / 9,
    position: 'relative',
    backgroundColor: lightSemanticSurfaces.secondary,
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  seasonBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radiusScale.xs,
  },
  seasonText: {
    color: '#FFF',
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  details: {
    padding: spacingScale.space4,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacingScale.space1,
  },
  title: {
    fontSize: typeScale.headingM.fontSize,
    lineHeight: typeScale.headingM.lineHeight,
    fontWeight: '700',
    color: lightSemanticContent.primary,
    flex: 1,
  },
  countBadge: {
    fontSize: typeScale.caption.fontSize,
    fontWeight: '600',
    color: lightSemanticContent.tertiary,
    marginLeft: spacingScale.space2,
  },
  description: {
    fontSize: typeScale.bodyS.fontSize,
    lineHeight: typeScale.bodyS.lineHeight,
    color: lightSemanticContent.secondary,
    marginBottom: spacingScale.space3,
  },
  cta: {
    fontSize: typeScale.labelS.fontSize,
    fontWeight: '700',
    color: brandPalette.primary,
  },
});
