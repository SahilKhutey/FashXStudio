/**
 * FashXStudio — Rating Component (Phase 05 - Level 2 Core UI)
 *
 * 5-star rating display with half-star increments, interactive rating selection,
 * numeric score chip, and optional review count.
 * Consumes Phase 02 brand accent and status warning tokens.
 */

import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  brandPalette,
  neutralPrimitives,
  spacingScale,
  typeScale,
} from '../tokens/primitives';
import { lightSemanticContent } from '../tokens/semantic';
import type { RatingProps } from './types';

export function Rating({
  value,
  maxStars = 5,
  allowHalf = true,
  showScore = true,
  isReadOnly = true,
  onChange,
  ratingCount,
  testID,
}: RatingProps) {
  const stars = Array.from({ length: maxStars }, (_, i) => i + 1);

  const getStarChar = (starIndex: number) => {
    if (value >= starIndex) return '★';
    if (allowHalf && value >= starIndex - 0.5) return '⯪';
    return '☆';
  };

  const handleStarPress = (starIndex: number) => {
    if (isReadOnly || !onChange) return;
    onChange(starIndex);
  };

  return (
    <View
      style={styles.container}
      accessibilityRole="text"
      accessibilityLabel={`Rating: ${value.toFixed(1)} out of ${maxStars} stars`}
      testID={testID}
    >
      <View style={styles.starRow}>
        {stars.map((starIndex) => (
          <Pressable
            key={starIndex}
            onPress={() => handleStarPress(starIndex)}
            disabled={isReadOnly}
            style={styles.starTouch}
            accessibilityRole={isReadOnly ? 'none' : 'button'}
            accessibilityLabel={`${starIndex} stars`}
          >
            <Text
              style={[
                styles.starText,
                {
                  color:
                    value >= starIndex - 0.5
                      ? brandPalette.accent
                      : neutralPrimitives.neutral300,
                },
              ]}
            >
              {getStarChar(starIndex)}
            </Text>
          </Pressable>
        ))}
      </View>

      {showScore && (
        <Text style={styles.scoreText}>{value.toFixed(1)}</Text>
      )}

      {ratingCount !== undefined && (
        <Text style={styles.countText}>({ratingCount})</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacingScale.space2,
  },
  starRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  starTouch: {
    padding: 2,
    minWidth: 24,
    minHeight: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  starText: {
    fontSize: 18,
    lineHeight: 20,
  },
  scoreText: {
    fontSize: typeScale.labelM.fontSize,
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
  countText: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.tertiary,
  },
});
