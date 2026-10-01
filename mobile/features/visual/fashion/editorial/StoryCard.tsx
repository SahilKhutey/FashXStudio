/**
 * FashXStudio — StoryCard Component (Phase 06 - Fashion Content)
 *
 * Editorial fashion narrative card emphasizing photography,
 * headline, category kicker, and author attribution (Section 6.22 - 6.24).
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
import type { FashionStory } from '../types';

export interface StoryCardProps {
  story: FashionStory;
  onPress?: () => void;
  testID?: string;
}

export function StoryCard({ story, onPress, testID }: StoryCardProps) {
  const { title, subtitle, heroImageUri, author, category, publishedDate } = story;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        elevationShadows[2],
        pressed && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Story: ${title} by ${author}`}
      testID={testID}
    >
      <View style={styles.mediaContainer}>
        <Image source={{ uri: heroImageUri }} style={styles.image} resizeMode="cover" />
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryText}>{category}</Text>
        </View>
      </View>

      <View style={styles.details}>
        <Text style={styles.title} numberOfLines={2}>
          {title}
        </Text>
        {subtitle && (
          <Text style={styles.subtitle} numberOfLines={2}>
            {subtitle}
          </Text>
        )}
        <View style={styles.metaRow}>
          <Text style={styles.author} numberOfLines={1}>
            {author}
          </Text>
          <Text style={styles.date}>{publishedDate}</Text>
        </View>
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
  mediaContainer: {
    width: '100%',
    aspectRatio: 16 / 9,
    backgroundColor: lightSemanticSurfaces.secondary,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  categoryBadge: {
    position: 'absolute',
    top: 12,
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
  },
  details: {
    padding: spacingScale.space4,
  },
  title: {
    fontSize: typeScale.headingM.fontSize,
    lineHeight: typeScale.headingM.lineHeight,
    fontWeight: '700',
    color: lightSemanticContent.primary,
    marginBottom: spacingScale.space1,
  },
  subtitle: {
    fontSize: typeScale.bodyS.fontSize,
    lineHeight: typeScale.bodyS.lineHeight,
    color: lightSemanticContent.secondary,
    marginBottom: spacingScale.space3,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: lightSemanticBorders.subtle,
    paddingTop: spacingScale.space2,
  },
  author: {
    fontSize: typeScale.caption.fontSize,
    fontWeight: '600',
    color: lightSemanticContent.tertiary,
    flex: 1,
  },
  date: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.tertiary,
    marginLeft: spacingScale.space2,
  },
});
