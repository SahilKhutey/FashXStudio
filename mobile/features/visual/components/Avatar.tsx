/**
 * FashXStudio — Avatar Component (Phase 05 - L2 Core UI)
 *
 * User, creator, and brand profile avatar supporting image,
 * fallback initials, and standardized sizes (Section 5.22).
 */

import React from 'react';
import {
  Image,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  radiusScale,
  typeScale,
} from '../tokens/primitives';
import {
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { AvatarProps } from './types';

export function Avatar({
  imageUri,
  initials,
  size = 'md',
  accessibilityLabel = 'User Avatar',
  testID,
}: AvatarProps) {
  const getDimension = () => {
    switch (size) {
      case 'sm':
        return 32;
      case 'lg':
        return 56;
      case 'md':
      default:
        return 40;
    }
  };

  const dimension = getDimension();

  return (
    <View
      style={[
        styles.container,
        {
          width: dimension,
          height: dimension,
          borderRadius: radiusScale.full,
        },
      ]}
      accessibilityRole="image"
      accessibilityLabel={accessibilityLabel}
      testID={testID}
    >
      {imageUri ? (
        <Image
          source={{ uri: imageUri }}
          style={{ width: dimension, height: dimension, borderRadius: radiusScale.full }}
          resizeMode="cover"
        />
      ) : (
        <Text
          style={[
            styles.initials,
            {
              fontSize: dimension * 0.4,
              lineHeight: dimension * 0.45,
            },
          ]}
        >
          {initials || 'FX'}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: lightSemanticSurfaces.tertiary,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  initials: {
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
});
