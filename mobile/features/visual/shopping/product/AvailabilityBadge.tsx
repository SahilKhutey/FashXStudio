/**
 * AvailabilityBadge Component — Phase 07 (Section 7.30).
 *
 * Renders real-time inventory and fulfillment states:
 * In Stock, Low Stock, Out of Stock, Unavailable, Pre-order.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { ProductAvailabilityState } from "../types";

export interface AvailabilityBadgeProps {
  availability: ProductAvailabilityState;
  stockCount?: number;
}

export const AvailabilityBadge: React.FC<AvailabilityBadgeProps> = ({
  availability,
  stockCount,
}) => {
  const getBadgeConfig = () => {
    switch (availability) {
      case "in_stock":
        return {
          dotColor: defaultDesignTokens.status.success,
          textColor: defaultDesignTokens.status.success,
          label: "In Stock",
        };
      case "low_stock":
        return {
          dotColor: defaultDesignTokens.status.warning,
          textColor: defaultDesignTokens.status.warning,
          label: stockCount ? `Only ${stockCount} left` : "Low Stock",
        };
      case "out_of_stock":
        return {
          dotColor: defaultDesignTokens.status.error,
          textColor: defaultDesignTokens.status.error,
          label: "Out of Stock",
        };
      case "preorder":
        return {
          dotColor: defaultDesignTokens.brand.accent,
          textColor: defaultDesignTokens.brand.accent,
          label: "Pre-order",
        };
      case "unavailable":
      default:
        return {
          dotColor: defaultDesignTokens.neutral.neutral500,
          textColor: defaultDesignTokens.neutral.neutral500,
          label: "Unavailable",
        };
    }
  };

  const { dotColor, textColor, label } = getBadgeConfig();

  return (
    <View style={styles.container}>
      <View style={[styles.dot, { backgroundColor: dotColor }]} />
      <Text style={[styles.label, { color: textColor }]}>{label}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
  },
  label: {
    fontSize: 12,
    fontWeight: "600",
    letterSpacing: 0.2,
  },
});
