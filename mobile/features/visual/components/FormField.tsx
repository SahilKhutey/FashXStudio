/**
 * FashXStudio — FormField Component (Phase 05 - Level 2 Core UI)
 *
 * Composite form field wrapper providing consistent label alignment,
 * required indicator, helper text, and accessible error message regions.
 * Consumes Phase 02 status and typography tokens.
 */

import React from 'react';
import {
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  spacingScale,
  statusPalette,
  typeScale,
} from '../tokens/primitives';
import { lightSemanticContent } from '../tokens/semantic';
import type { FormFieldProps } from './types';

export function FormField({
  fieldId,
  label,
  children,
  isRequired = false,
  helperText,
  errorText,
  state = 'default',
  testID,
}: FormFieldProps) {
  const isError = state === 'error' || !!errorText;

  return (
    <View style={styles.container} testID={testID} nativeID={fieldId}>
      <View style={styles.labelRow}>
        <Text style={styles.label}>
          {label}
          {isRequired && <Text style={styles.requiredStar}> *</Text>}
        </Text>
      </View>

      <View style={styles.inputSlot}>{children}</View>

      {isError && errorText ? (
        <Text
          style={styles.errorText}
          accessibilityRole="alert"
          accessibilityLiveRegion="polite"
        >
          {errorText}
        </Text>
      ) : helperText ? (
        <Text style={styles.helperText}>{helperText}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    marginBottom: spacingScale.space4,
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacingScale.space1,
  },
  label: {
    fontSize: typeScale.labelM.fontSize,
    lineHeight: typeScale.labelM.lineHeight,
    fontWeight: '600',
    color: lightSemanticContent.primary,
  },
  requiredStar: {
    color: statusPalette.error,
    fontWeight: '700',
  },
  inputSlot: {
    width: '100%',
  },
  helperText: {
    marginTop: spacingScale.space1,
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.tertiary,
  },
  errorText: {
    marginTop: spacingScale.space1,
    fontSize: typeScale.caption.fontSize,
    color: statusPalette.error,
    fontWeight: '500',
  },
});
