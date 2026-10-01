/**
 * ConfirmationTemplate Component — Phase 07 (Section 7.47).
 *
 * Post-order confirmation screen displaying:
 * - Checkmark confirmation header
 * - Order number & estimated delivery
 * - Item count & total payment
 * - Action triggers: View Order & Continue Shopping
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { ConfirmationTemplateSpec } from "../types";
import { Button } from "../../components/Button";

export interface ConfirmationTemplateProps {
  spec: ConfirmationTemplateSpec;
  onViewOrder: (orderId: string) => void;
  onContinueShopping: () => void;
}

export const ConfirmationTemplate: React.FC<ConfirmationTemplateProps> = ({
  spec,
  onViewOrder,
  onContinueShopping,
}) => {
  return (
    <View style={styles.container}>
      {/* Success Badge */}
      <View style={styles.successIconCircle}>
        <Text style={styles.successCheck}>✓</Text>
      </View>

      <Text style={styles.title}>Order Confirmed!</Text>
      <Text style={styles.subtitle}>
        Thank you for your order. We’ve received your request and our artisans are preparing your
        garments.
      </Text>

      {/* Order Info Card */}
      <View style={styles.orderCard}>
        <View style={styles.orderRow}>
          <Text style={styles.label}>Order Number</Text>
          <Text style={styles.valueBold}>{spec.orderNumber}</Text>
        </View>

        <View style={styles.orderRow}>
          <Text style={styles.label}>Estimated Delivery</Text>
          <Text style={styles.valueHighlight}>{spec.estimatedDelivery}</Text>
        </View>

        <View style={styles.orderRow}>
          <Text style={styles.label}>Total Amount ({spec.itemsCount} items)</Text>
          <Text style={styles.valueTotal}>
            {spec.currencySymbol}
            {spec.totalAmount.toLocaleString()}
          </Text>
        </View>
      </View>

      {/* Action CTAs */}
      <View style={styles.actions}>
        <Button
          label="View Order Details"
          variant="primary"
          size="lg"
          fullWidth
          onPress={() => onViewOrder(spec.orderId)}
        />
        <Button
          label="Continue Shopping"
          variant="outline"
          size="lg"
          fullWidth
          onPress={onContinueShopping}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
    gap: 16,
  },
  successIconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: defaultDesignTokens.status.success,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 8,
  },
  successCheck: {
    fontSize: 32,
    fontWeight: "800",
    color: defaultDesignTokens.surfaces.surfaceLight,
  },
  title: {
    fontSize: 24,
    fontWeight: "800",
    color: defaultDesignTokens.neutral.neutral900,
    textAlign: "center",
  },
  subtitle: {
    fontSize: 14,
    color: defaultDesignTokens.neutral.neutral600,
    textAlign: "center",
    lineHeight: 20,
    paddingHorizontal: 12,
  },
  orderCard: {
    width: "100%",
    padding: 16,
    borderRadius: 12,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    gap: 12,
    marginVertical: 12,
  },
  orderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  label: {
    fontSize: 13,
    color: defaultDesignTokens.neutral.neutral600,
  },
  valueBold: {
    fontSize: 14,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
  },
  valueHighlight: {
    fontSize: 14,
    fontWeight: "600",
    color: defaultDesignTokens.brand.primary,
  },
  valueTotal: {
    fontSize: 16,
    fontWeight: "800",
    color: defaultDesignTokens.neutral.neutral900,
  },
  actions: {
    width: "100%",
    gap: 12,
    marginTop: 8,
  },
});
