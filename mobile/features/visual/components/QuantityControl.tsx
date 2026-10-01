/**
 * FashXStudio — QuantityControl Component (Phase 05 - L2 Core UI)
 *
 * Stepper control for cart and wardrobe quantity adjustment with
 * minimum, maximum, and disabled state enforcement (Section 5.42).
 */

import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  neutralPrimitives,
  radiusScale,
  spacingScale,
  typeScale,
} from '../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { QuantityControlProps } from './types';

export function QuantityControl({
  value,
  onChange,
  minValue = 1,
  maxValue = 99,
  isDisabled = false,
  testID,
}: QuantityControlProps) {
  const canDecrement = !isDisabled && value > minValue;
  const canIncrement = !isDisabled && value < maxValue;

  const handleDecrement = () => {
    if (canDecrement) onChange(value - 1);
  };

  const handleIncrement = () => {
    if (canIncrement) onChange(value + 1);
  };

  return (
    <View
      style={styles.container}
      accessibilityRole="none"
      testID={testID}
    >
      <Pressable
        onPress={handleDecrement}
        disabled={!canDecrement}
        style={[
          styles.button,
          !canDecrement && styles.buttonDisabled,
        ]}
        accessibilityRole="button"
        accessibilityLabel="Decrease quantity"
      >
        <Text style={[styles.buttonText, !canDecrement && styles.textDisabled]}>
          −
        </Text>
      </Pressable>

      <View style={styles.valueDisplay}>
        <Text
          style={styles.valueText}
          accessibilityLabel={`Quantity ${value}`}
        >
          {value}
        </Text>
      </View>

      <Pressable
        onPress={handleIncrement}
        disabled={!canIncrement}
        style={[
          styles.button,
          !canIncrement && styles.buttonDisabled,
        ]}
        accessibilityRole="button"
        accessibilityLabel="Increase quantity"
      >
        <Text style={[styles.buttonText, !canIncrement && styles.textDisabled]}>
          +
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: lightSemanticBorders.default,
    borderRadius: radiusScale.sm,
    backgroundColor: lightSemanticSurfaces.primary,
    overflow: 'hidden',
    minHeight: 44, // WCAG minimum
    alignSelf: 'flex-start',
  },
  button: {
    minWidth: 44,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: lightSemanticSurfaces.secondary,
  },
  buttonDisabled: {
    opacity: 0.4,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
  textDisabled: {
    color: neutralPrimitives.neutral400,
  },
  valueDisplay: {
    minWidth: 40,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacingScale.space2,
  },
  valueText: {
    fontSize: typeScale.labelM.fontSize,
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
});
