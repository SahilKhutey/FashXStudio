/**
 * FashXStudio — LookCard Component (Phase 06 - Fashion Content)
 *
 * Curated fashion look presentation emphasizing complete visual styling,
 * piece tally count, and curator attribution (Section 6.10).
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
import type { LookItem } from '../types';

export interface LookCardProps {
  look: LookItem;
  onPress?: () => void;
  onSaveToggle?: () => void;
  testID?: string;
}

export function LookCard({
  look,
  onPress,
  onSaveToggle,
  testID,
}: LookCardProps) {
  const { title, styleName, heroImageUri, itemsCount, isSaved = false, curatorName } = look;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        elevationShadows[1],
        pressed && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Look: ${title}, ${styleName} style with ${itemsCount} pieces`}
      testID={testID}
    >
      <View style={styles.mediaContainer}>
        <Image
          source={{ uri: heroImageUri }}
          style={styles.image}
          resizeMode="cover"
        />

        <View style={styles.tagBadge}>
          <Text style={styles.tagText}>{styleName}</Text>
        </View>

        {onSaveToggle && (
          <Pressable
            onPress={onSaveToggle}
            style={styles.saveButton}
            accessibilityRole="button"
            accessibilityLabel={isSaved ? 'Remove look from saved' : 'Save look'}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={[styles.saveIcon, isSaved && styles.saveIconActive]}>
              {isSaved ? '❤️' : '🤍'}
            </Text>
          </Pressable>
        )}
      </View>

      <View style={styles.details}>
        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>
        <Text style={styles.subtitle} numberOfLines={1}>
          {itemsCount} pieces {curatorName ? `• Curated by ${curatorName}` : ''}
        </Text>
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
    aspectRatio: 4 / 5,
    backgroundColor: lightSemanticSurfaces.secondary,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  tagBadge: {
    position: 'absolute',
    bottom: 8,
    left: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radiusScale.xs,
  },
  tagText: {
    color: '#FFF',
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  saveButton: {
    position: 'absolute',
    top: 8,
    right: 8,
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
  title: {
    fontSize: typeScale.labelM.fontSize,
    lineHeight: typeScale.labelM.lineHeight,
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
  subtitle: {
    fontSize: typeScale.caption.fontSize,
    lineHeight: typeScale.caption.lineHeight,
    color: lightSemanticContent.secondary,
    marginTop: 2,
  },
});
