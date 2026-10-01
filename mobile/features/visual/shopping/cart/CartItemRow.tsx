/**
 * CartItemRow Component — Phase 07 (Section 7.36 - 7.39).
 *
 * Renders individual line item in cart with variant summary,
 * unit price, quantity increment/decrement, and remove action.
 */

import React from "react";
import { Image, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { CartItem } from "../types";
import { Price } from "../../components/Price";
import { QuantityControl } from "../../components/QuantityControl";

export interface CartItemRowProps {
  item: CartItem;
  onUpdateQuantity: (newQuantity: number) => void;
  onRemoveItem: () => void;
}

export const CartItemRow: React.FC<CartItemRowProps> = ({
  item,
  onUpdateQuantity,
  onRemoveItem,
}) => {
  const variantLabels = Object.entries(item.selectedVariants)
    .map(([key, val]) => `${key.toUpperCase()}: ${val.toUpperCase()}`)
    .join(" · ");

  return (
    <View style={styles.container}>
      {/* Product Thumbnail */}
      <Image source={{ uri: item.mediaUri }} style={styles.thumbnail} resizeMode="cover" />

      {/* Details */}
      <View style={styles.content}>
        <View style={styles.headerRow}>
          <Text style={styles.brand}>{item.brand}</Text>
          <TouchableOpacity
            accessibilityLabel={`Remove ${item.title} from cart`}
            onPress={onRemoveItem}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={styles.removeText}>✕</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.title} numberOfLines={2}>
          {item.title}
        </Text>

        {variantLabels ? <Text style={styles.variants}>{variantLabels}</Text> : null}

        <View style={styles.footerRow}>
          <Price spec={item.totalPrice} size="sm" />
          <QuantityControl
            quantity={item.quantity}
            min={1}
            max={10}
            onChange={onUpdateQuantity}
            size="sm"
          />
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    padding: 12,
    borderRadius: 12,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
    gap: 12,
    alignItems: "center",
  },
  thumbnail: {
    width: 80,
    height: 106,
    borderRadius: 8,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
  },
  content: {
    flex: 1,
    gap: 4,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  brand: {
    fontSize: 11,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral500,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  removeText: {
    fontSize: 14,
    color: defaultDesignTokens.neutral.neutral400,
    fontWeight: "600",
  },
  title: {
    fontSize: 14,
    fontWeight: "600",
    color: defaultDesignTokens.neutral.neutral900,
  },
  variants: {
    fontSize: 12,
    color: defaultDesignTokens.neutral.neutral600,
  },
  footerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 6,
  },
});
