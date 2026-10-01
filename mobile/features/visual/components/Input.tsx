/**
 * FashXStudio — Input Primitive (Phase 05)
 *
 * Production single-line TextInput supporting text, search, email,
 * password, number, and phone types. Includes floating or top label,
 * helper text, error text, clear button, leading/trailing icons,
 * and focus ring styling. Consumes Phase 02 design tokens.
 */

import React, { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import {
  brandPalette,
  neutralPrimitives,
  radiusScale,
  spacingScale,
  statusPalette,
  typeScale,
} from '../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { InputProps } from './types';

export function Input({
  inputType = 'text',
  value,
  onChangeText,
  label,
  placeholder,
  helperText,
  errorText,
  isDisabled = false,
  isReadOnly = false,
  isRequired = false,
  leadingIcon,
  trailingIcon,
  showClearButton = true,
  onClear,
  accessibilityLabel,
  testID,
}: InputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  const isPassword = inputType === 'password';
  const hasError = !!errorText;

  const getBorderColor = () => {
    if (hasError) return statusPalette.error;
    if (isFocused) return brandPalette.secondary;
    return lightSemanticBorders.default;
  };

  const handleClear = () => {
    if (onChangeText) onChangeText('');
    if (onClear) onClear();
  };

  return (
    <View style={styles.container}>
      {label && (
        <View style={styles.labelRow}>
          <Text style={styles.label}>
            {label}
            {isRequired && <Text style={styles.requiredStar}> *</Text>}
          </Text>
        </View>
      )}

      <View
        style={[
          styles.inputContainer,
          {
            borderColor: getBorderColor(),
            borderWidth: isFocused ? 2 : 1,
            backgroundColor: isDisabled
              ? neutralPrimitives.neutral100
              : lightSemanticSurfaces.primary,
          },
        ]}
      >
        {leadingIcon && <Text style={styles.leadingIcon}>{leadingIcon}</Text>}

        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={lightSemanticContent.tertiary}
          editable={!isDisabled && !isReadOnly}
          secureTextEntry={isPassword && !isPasswordVisible}
          keyboardType={
            inputType === 'number'
              ? 'numeric'
              : inputType === 'email'
              ? 'email-address'
              : inputType === 'phone'
              ? 'phone-pad'
              : 'default'
          }
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          style={[
            styles.input,
            isDisabled && { color: neutralPrimitives.neutral400 },
          ]}
          accessibilityLabel={accessibilityLabel || label || placeholder}
          accessibilityState={{ disabled: isDisabled }}
          testID={testID}
        />

        {showClearButton && value && value.length > 0 && !isDisabled && !isReadOnly && (
          <Pressable
            onPress={handleClear}
            style={styles.actionButton}
            accessibilityRole="button"
            accessibilityLabel="Clear text"
          >
            <Text style={styles.actionIcon}>✕</Text>
          </Pressable>
        )}

        {isPassword && (
          <Pressable
            onPress={() => setIsPasswordVisible(!isPasswordVisible)}
            style={styles.actionButton}
            accessibilityRole="button"
            accessibilityLabel={isPasswordVisible ? 'Hide password' : 'Show password'}
          >
            <Text style={styles.actionIcon}>{isPasswordVisible ? '👁' : '👁‍🗨'}</Text>
          </Pressable>
        )}

        {trailingIcon && !isPassword && (
          <Text style={styles.trailingIcon}>{trailingIcon}</Text>
        )}
      </View>

      {hasError ? (
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
    marginBottom: spacingScale.space3,
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
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 48, // WCAG touch target >= 44px
    borderRadius: radiusScale.sm,
    paddingHorizontal: spacingScale.space3,
  },
  input: {
    flex: 1,
    height: '100%',
    fontSize: typeScale.bodyM.fontSize,
    color: lightSemanticContent.primary,
    paddingVertical: spacingScale.space2,
  },
  leadingIcon: {
    fontSize: 16,
    marginRight: spacingScale.space2,
    color: lightSemanticContent.tertiary,
  },
  trailingIcon: {
    fontSize: 16,
    marginLeft: spacingScale.space2,
    color: lightSemanticContent.tertiary,
  },
  actionButton: {
    minWidth: 32,
    minHeight: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacingScale.space1,
  },
  actionIcon: {
    fontSize: 14,
    color: lightSemanticContent.secondary,
  },
  helperText: {
    marginTop: spacingScale.space1,
    fontSize: typeScale.caption.fontSize,
    lineHeight: typeScale.caption.lineHeight,
    color: lightSemanticContent.tertiary,
  },
  errorText: {
    marginTop: spacingScale.space1,
    fontSize: typeScale.caption.fontSize,
    lineHeight: typeScale.caption.lineHeight,
    color: statusPalette.error,
    fontWeight: '500',
  },
});
