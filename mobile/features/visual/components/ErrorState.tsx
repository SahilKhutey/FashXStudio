/**
 * FashXStudio — ErrorState Component (Phase 05 - L2 Core UI)
 *
 * Standardized error recovery view with a meaningful message,
 * primary retry button, and secondary recovery destination (Section 5.35).
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  spacingScale,
  statusPalette,
  typeScale,
} from '../tokens/primitives';
import { lightSemanticContent } from '../tokens/semantic';
import { Button } from './Button';
import type { ErrorStateProps } from './types';

export function ErrorState({
  title = 'Something went wrong.',
  message,
  retryLabel = 'Try Again',
  onRetry,
  recoveryLabel,
  onRecovery,
  testID,
}: ErrorStateProps) {
  return (
    <View
      style={styles.container}
      accessibilityRole="alert"
      accessibilityLiveRegion="assertive"
      testID={testID}
    >
      <Text style={styles.icon}>⚠️</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>

      <View style={styles.buttonRow}>
        {onRetry && (
          <Button
            label={retryLabel}
            onPress={onRetry}
            variant="primary"
            size="md"
          />
        )}
        {recoveryLabel && onRecovery && (
          <Button
            label={recoveryLabel}
            onPress={onRecovery}
            variant="outline"
            size="md"
          />
        )}
      </View>
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
    fontSize: 44,
    marginBottom: spacingScale.space3,
  },
  title: {
    fontSize: typeScale.headingM.fontSize,
    lineHeight: typeScale.headingM.lineHeight,
    fontWeight: '700',
    color: statusPalette.error,
    textAlign: 'center',
    marginBottom: spacingScale.space2,
  },
  message: {
    fontSize: typeScale.bodyM.fontSize,
    lineHeight: typeScale.bodyM.lineHeight,
    color: lightSemanticContent.secondary,
    textAlign: 'center',
    maxWidth: 380,
    marginBottom: spacingScale.space6,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: spacingScale.space3,
    alignItems: 'center',
  },
});
