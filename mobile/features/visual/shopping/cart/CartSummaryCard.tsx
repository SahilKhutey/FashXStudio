/**
 * CartSummaryCard Component — Phase 07 (Section 7.37 & 7.38).
 *
 * Renders authoritative subtotal, delivery fee, discounts,
 * total amount, and checkout CTA button.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { CartSummary } from "../types";
import { Button } from "../../components/Button";

export interface CartSummaryCardProps {
  summary: CartSummary;
  onProceedToCheckout?: () => void;
  isLoading?: boolean;
}

export const CartSummaryCard: React.FC<CartSummaryCardProps> = ({
  summary,
  onProceedToCheckout,
  isLoading,
}) => {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Order Summary</Text>

      <View style={styles.row}>
        <Text style={styles.label}>Subtotal ({summary.itemCount} items)</Text>
        <Text style={styles.value}>
          {summary.currencySymbol}
          {summary.subtotal.toLocaleString()}
        </Text>
      </View>

      {summary.discount > 0 ? (
        <View style={styles.row}>
          <Text style={[styles.label, styles.discountLabel]}>Discount</Text>
          <Text style={[styles.value, styles.discountValue]}>
            -{summary.currencySymbol}
            {summary.discount.toLocaleString()}
          </Text>
        </View>
      ) : null}

      <View style={styles.row}>
        <Text style={styles.label}>Delivery</Text>
        <Text style={styles.value}>
          {summary.deliveryFee === 0 ? "FREE" : `${summary.currencySymbol}${summary.deliveryFee}`}
        </Text>
      </View>

      <View style={styles.divider} />

      <View style={styles.row}>
        <Text style={styles.totalLabel}>Total</Text>
        <Text style={styles.totalValue}>
          {summary.currencySymbol}
          {summary.total.toLocaleString()}
        </Text>
      </View>

      {onProceedToCheckout ? (
        <Button
          label="Proceed to Checkout"
          variant="primary"
          size="lg"
          fullWidth
          loading={isLoading}
          onPress={onProceedToCheckout}
          style={styles.checkoutButton}
        />
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
    gap: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
    marginBottom: 4,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  label: {
    fontSize: 14,
    color: defaultDesignTokens.neutral.neutral600,
  },
  value: {
    fontSize: 14,
    fontWeight: "600",
    color: defaultDesignTokens.neutral.neutral800,
  },
  discountLabel: {
    color: defaultDesignTokens.status.success,
  },
  discountValue: {
    color: defaultDesignTokens.status.success,
    fontWeight: "700",
  },
  divider: {
    height: 1,
    backgroundColor: defaultDesignTokens.neutral.neutral200,
    marginVertical: 4,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
  },
  totalValue: {
    fontSize: 18,
    fontWeight: "800",
    color: defaultDesignTokens.brand.primary,
  },
  checkoutButton: {
    marginTop: 8,
  },
});
