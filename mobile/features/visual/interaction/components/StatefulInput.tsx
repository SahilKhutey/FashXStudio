/**
 * StatefulInput — Production accessible form input (Section 15.12 - 15.15).
 *
 * Implements states: empty, focus, filled, valid, invalid, disabled.
 * Provides contextual error messages and actionable fix guidance.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TextInputProps,
  StyleProp,
  ViewStyle,
} from 'react-native';

interface StatefulInputProps extends TextInputProps {
  label: string;
  fieldId: string;
  errorMessage?: string | null;
  guidance?: string | null;
  isRequired?: boolean;
  isDisabled?: boolean;
  containerStyle?: StyleProp<ViewStyle>;
}

export const StatefulInput: React.FC<StatefulInputProps> = ({
  label,
  fieldId,
  errorMessage,
  guidance,
  isRequired = false,
  isDisabled = false,
  containerStyle,
  value,
  onChangeText,
  placeholder,
  ...rest
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const isError = Boolean(errorMessage);

  return (
    <View style={[styles.fieldContainer, containerStyle]}>
      {/* Field Label */}
      <View style={styles.labelRow}>
        <Text style={styles.labelText}>
          {label}
          {isRequired && <Text style={styles.requiredAsterisk}> *</Text>}
        </Text>
      </View>

      {/* Input Surface */}
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor="#9CA3AF"
        editable={!isDisabled}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        accessibilityLabel={label}
        accessibilityState={{
          disabled: isDisabled,
        }}
        accessibilityHint={guidance || undefined}
        style={[
          styles.inputBase,
          isFocused && styles.inputFocused,
          isError && styles.inputError,
          isDisabled && styles.inputDisabled,
        ]}
        {...rest}
      />

      {/* Contextual Error & Fix Guidance (Section 15.13 & 15.14) */}
      {isError && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>⚠ {errorMessage}</Text>
          {guidance && <Text style={styles.guidanceText}>{guidance}</Text>}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  fieldContainer: {
    width: '100%',
    marginBottom: 16,
  },
  labelRow: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  labelText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  requiredAsterisk: {
    color: '#DC2626',
    fontWeight: '700',
  },
  inputBase: {
    minHeight: 44, // WCAG 2.1 AA touch target
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 15,
    color: '#111827',
  },
  inputFocused: {
    borderColor: '#6366F1',
    borderWidth: 2,
  },
  inputError: {
    borderColor: '#DC2626',
    borderWidth: 2,
    backgroundColor: '#FEF2F2',
  },
  inputDisabled: {
    backgroundColor: '#F3F4F6',
    borderColor: '#E5E7EB',
    color: '#9CA3AF',
  },
  errorContainer: {
    marginTop: 6,
    gap: 2,
  },
  errorText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#DC2626',
  },
  guidanceText: {
    fontSize: 12,
    color: '#4B5563',
  },
});
