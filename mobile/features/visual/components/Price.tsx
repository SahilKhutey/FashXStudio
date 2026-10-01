/**
 * FashXStudio — Price Component (Phase 05 - L2 Core UI)
 *
 * Standardized price display component with currency formatting,
 * strikethrough original price, and discount percentage (Section 5.41).
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  spacingScale,
  statusPalette,
  typeScale,
} from '../tokens/primitives';
import { lightSemanticContent } from '../tokens/semantic';
import type { PriceProps } from './types';

export function Price({
  amount,
  originalAmount,
  currencySymbol = '₹',
  discountPercentage,
  size = 'md',
  testID,
}: PriceProps) {
  const isSm = size === 'sm';
  const isLg = size === 'lg';

  const formatAmount = (val: number) => {
    return val.toLocaleString('en-IN');
  };

  const calculatedDiscount =
    discountPercentage !== undefined
      ? discountPercentage
      : originalAmount && originalAmount > amount
      ? Math.round(((originalAmount - amount) / originalAmount) * 100)
      : null;

  return (
    <View
      style={styles.container}
      accessibilityRole="text"
      accessibilityLabel={`Price: ${currencySymbol}${formatAmount(amount)}${
        originalAmount ? `, originally ${currencySymbol}${formatAmount(originalAmount)}` : ''
      }`}
      testID={testID}
    >
      <Text
        style={[
          styles.currentPrice,
          isSm ? styles.currentPrice_sm : isLg ? styles.currentPrice_lg : styles.currentPrice_md,
        ]}
      >
        {currencySymbol}
        {formatAmount(amount)}
      </Text>

      {originalAmount && originalAmount > amount && (
        <Text
          style={[
            styles.originalPrice,
            isSm ? styles.originalPrice_sm : styles.originalPrice_md,
          ]}
        >
          {currencySymbol}
          {formatAmount(originalAmount)}
        </Text>
      )}

      {calculatedDiscount !== null && calculatedDiscount > 0 && (
        <View style={styles.discountBadge}>
          <Text style={styles.discountText}>{calculatedDiscount}% OFF</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: spacingScale.space2,
  },
  currentPrice: {
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
  currentPrice_sm: {
    fontSize: typeScale.labelM.fontSize,
  },
  currentPrice_md: {
    fontSize: typeScale.headingS.fontSize,
  },
  currentPrice_lg: {
    fontSize: typeScale.headingL.fontSize,
  },
  originalPrice: {
    textDecorationLine: 'line-through',
    color: lightSemanticContent.tertiary,
    fontWeight: '400',
  },
  originalPrice_sm: {
    fontSize: typeScale.caption.fontSize,
  },
  originalPrice_md: {
    fontSize: typeScale.bodyS.fontSize,
  },
  discountBadge: {
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 4,
  },
  discountText: {
    fontSize: 10,
    fontWeight: '700',
    color: statusPalette.success,
  },
});
