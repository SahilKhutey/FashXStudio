/**
 * FashXStudio — EmptyState Component (Phase 05 - L2 Core UI)
 *
 * Consistent empty state screen component explaining what is empty,
 * why it matters, and offering a clear next-step CTA (Section 5.34).
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  spacingScale,
  typeScale,
} from '../tokens/primitives';
import { lightSemanticContent } from '../tokens/semantic';
import { Button } from './Button';
import type { EmptyStateProps } from './types';

export function EmptyState({
  icon = '♡',
  title,
  description,
  actionLabel,
  onAction,
  testID,
}: EmptyStateProps) {
  return (
    <View style={styles.container} testID={testID}>
      <Text style={styles.icon}>{icon}</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.description}>{description}</Text>

      {actionLabel && onAction && (
        <View style={styles.actionContainer}>
          <Button
            label={actionLabel}
            onPress={onAction}
            variant="primary"
            size="md"
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacingScale.space8,
    paddingHorizontal: spacingScale.space6,
    width: '100%',
  },
  icon: {
    fontSize: 48,
    marginBottom: spacingScale.space3,
    color: lightSemanticContent.tertiary,
  },
  title: {
    fontSize: typeScale.headingM.fontSize,
    lineHeight: typeScale.headingM.lineHeight,
    fontWeight: '700',
    color: lightSemanticContent.primary,
    textAlign: 'center',
    marginBottom: spacingScale.space2,
  },
  description: {
    fontSize: typeScale.bodyM.fontSize,
    lineHeight: typeScale.bodyM.lineHeight,
    color: lightSemanticContent.secondary,
    textAlign: 'center',
    maxWidth: 360,
    marginBottom: spacingScale.space6,
  },
  actionContainer: {
    minWidth: 180,
  },
});
