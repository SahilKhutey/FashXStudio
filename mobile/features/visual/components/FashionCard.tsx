/**
 * FashXStudio — FashionCard Component (Phase 05 - L3 Composite)
 *
 * Editorial content card emphasizing fashion story visual,
 * category kicker, headline, and short narrative description (Section 5.52).
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
} from '../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { FashionCardProps } from './types';

export function FashionCard({
  storyId,
  title,
  category,
  imageUri,
  description,
  onPress,
  testID,
}: FashionCardProps) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        elevationShadows[1],
        pressed && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Fashion Story: ${title}, ${category}`}
      testID={testID}
    >
      <View style={styles.mediaContainer}>
        <Image
          source={{ uri: imageUri }}
          style={styles.image}
          resizeMode="cover"
        />
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryText}>{category}</Text>
        </View>
      </View>

      <View style={styles.details}>
        <Text style={styles.title} numberOfLines={2}>
          {title}
        </Text>
        {description && (
          <Text style={styles.description} numberOfLines={2}>
            {description}
          </Text>
        )}
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
  categoryBadge: {
    position: 'absolute',
    bottom: 12,
    left: 12,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radiusScale.xs,
  },
  categoryText: {
    color: '#FFF',
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  details: {
    padding: spacingScale.space4,
  },
  title: {
    fontSize: typeScale.headingM.fontSize,
    lineHeight: typeScale.headingM.lineHeight,
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
  description: {
    fontSize: typeScale.bodyS.fontSize,
    lineHeight: typeScale.bodyS.lineHeight,
    color: lightSemanticContent.secondary,
    marginTop: spacingScale.space1,
  },
});
