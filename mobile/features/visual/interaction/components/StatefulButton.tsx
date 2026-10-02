/**
 * StatefulButton — Production stateful button (Section 15.6 & 15.7).
 *
 * Implements states: default, hover, focus, pressed, loading, success, disabled.
 * Enforces >=44px touch target baseline and non-color-only state representation.
 */

import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  StyleProp,
  TextStyle,
  View,
} from 'react-native';
import { useInteractionState } from '../hooks/useInteractionState';

interface StatefulButtonProps {
  label: string;
  onPress: () => void;
  isLoading?: boolean;
  isDisabled?: boolean;
  isSuccess?: boolean;
  disabledExplanation?: string;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
  accessibilityLabel?: string;
}

export const StatefulButton: React.FC<StatefulButtonProps> = ({
  label,
  onPress,
  isLoading = false,
  isDisabled = false,
  isSuccess = false,
  disabledExplanation,
  variant = 'primary',
  style,
  textStyle,
  accessibilityLabel,
}) => {
  const { isPressed, isFocused, onPressIn, onPressOut, onFocus, onBlur } = useInteractionState({
    isDisabled: isDisabled || isSuccess,
    isLoading,
  });

  const getVariantStyles = (): { bg: string; text: string; border?: string } => {
    if (isDisabled) return { bg: '#E5E7EB', text: '#9CA3AF' };
    if (isSuccess) return { bg: '#059669', text: '#FFFFFF' };

    switch (variant) {
      case 'danger':
        return { bg: '#DC2626', text: '#FFFFFF' };
      case 'secondary':
        return { bg: '#FFFFFF', text: '#111827', border: '#D1D5DB' };
      case 'ghost':
        return { bg: 'transparent', text: '#111827' };
      case 'primary':
      default:
        return { bg: '#111827', text: '#FFFFFF' };
    }
  };

  const vStyles = getVariantStyles();

  return (
    <View style={styles.wrapper}>
      <TouchableOpacity
        onPress={onPress}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        onFocus={onFocus}
        onBlur={onBlur}
        disabled={isDisabled || isLoading || isSuccess}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel || label}
        accessibilityState={{
          disabled: isDisabled || isSuccess,
          busy: isLoading,
        }}
        accessibilityHint={disabledExplanation}
        style={[
          styles.buttonBase,
          {
            backgroundColor: vStyles.bg,
            borderColor: vStyles.border || 'transparent',
            borderWidth: vStyles.border ? 1 : 0,
            opacity: isPressed ? 0.85 : 1.0,
          },
          isFocused && styles.focusRing,
          style,
        ]}
      >
        {isLoading ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator color={vStyles.text} size="small" />
            <Text style={[styles.buttonText, { color: vStyles.text }, textStyle]}>Processing...</Text>
          </View>
        ) : isSuccess ? (
          <View style={styles.loadingRow}>
            <Text style={[styles.buttonText, { color: vStyles.text }, textStyle]}>✓ Complete</Text>
          </View>
        ) : (
          <Text style={[styles.buttonText, { color: vStyles.text }, textStyle]}>{label}</Text>
        )}
      </TouchableOpacity>

      {/* Disablement reason if provided (Section 15.7) */}
      {isDisabled && disabledExplanation && (
        <Text style={styles.disabledHintText}>{disabledExplanation}</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    width: '100%',
  },
  buttonBase: {
    minHeight: 44, // WCAG 2.1 AA touch target baseline
    minWidth: 44,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    fontSize: 15,
    fontWeight: '700',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  focusRing: {
    outlineWidth: 2,
    outlineColor: '#6366F1',
    outlineStyle: 'solid',
    outlineOffset: 2,
  },
  disabledHintText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'center',
  },
});
