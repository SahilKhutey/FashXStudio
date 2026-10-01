/**
 * FashXStudio — Link Component (Phase 05 - L2 Core UI)
 *
 * Accessible link component supporting internal routing, external links,
 * and keyboard/screen reader interaction (Section 5.10).
 */

import React from 'react';
import {
  Linking,
  Pressable,
  StyleSheet,
  Text,
} from 'react-native';

import { brandPalette, typeScale } from '../tokens/primitives';
import { lightSemanticContent } from '../tokens/semantic';
import type { LinkProps } from './types';

export function Link({
  href,
  label,
  onPress,
  isExternal = false,
  variant = 'default',
  accessibilityLabel,
  testID,
}: LinkProps) {
  const handlePress = () => {
    if (onPress) {
      onPress();
    } else if (isExternal) {
      Linking.openURL(href).catch((err) =>
        console.error('Failed to open external URL:', err),
      );
    }
  };

  const isUnderline = variant === 'underline';

  return (
    <Pressable
      onPress={handlePress}
      accessibilityRole="link"
      accessibilityLabel={accessibilityLabel || label}
      style={styles.pressable}
      testID={testID}
    >
      <Text
        style={[
          styles.text,
          {
            color:
              variant === 'subtle'
                ? lightSemanticContent.secondary
                : brandPalette.secondary,
            textDecorationLine: isUnderline ? 'underline' : 'none',
          },
        ]}
      >
        {label}
        {isExternal && ' ↗'}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pressable: {
    minHeight: 44, // WCAG target minimum
    justifyContent: 'center',
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: typeScale.labelM.fontSize,
    fontWeight: '600',
  },
});
