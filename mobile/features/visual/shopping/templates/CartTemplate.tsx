/**
 * CartTemplate Component — Phase 07 (Section 7.36 - 7.38).
 *
 * Full-screen shopping cart layout with:
 * - Cart Header & Item Count
 * - Cart Line Items with Quantity Controls
 * - Empty State with Explore CTA
 * - Order Summary Card & Checkout Trigger
 */

import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { CartTemplateSpec } from "../types";
import { CartItemRow } from "../cart/CartItemRow";
import { CartSummaryCard } from "../cart/CartSummaryCard";
import { EmptyState } from "../../components/EmptyState";
import { Button } from "../../components/Button";

export interface CartTemplateProps {
  spec: CartTemplateSpec;
  onUpdateQuantity: (itemId: string, newQuantity: number) => void;
  onRemoveItem: (itemId: string) => void;
  onProceedToCheckout: () => void;
  onExploreProducts: () => void;
  isUpdating?: boolean;
}

export const CartTemplate: React.FC<CartTemplateProps> = ({
  spec,
  onUpdateQuantity,
  onRemoveItem,
  onProceedToCheckout,
  onExploreProducts,
  isUpdating,
}) => {
  const { cart } = spec;
  const isEmpty = cart.items.length === 0;

  if (isEmpty) {
    return (
      <View style={styles.emptyContainer}>
        <EmptyState
          title="Your Shopping Cart is Empty"
          description="Looks like you haven't added any designer pieces or looks yet. Explore our curated collections."
          actionLabel="Explore Collections"
          onAction={onExploreProducts}
        />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Text style={styles.title}>Shopping Cart</Text>
        <Text style={styles.itemCount}>({cart.summary.itemCount} items)</Text>
      </View>

      {/* Cart Items List */}
      <View style={styles.itemsList}>
        {cart.items.map((item) => (
          <CartItemRow
            key={item.itemId}
            item={item}
            onUpdateQuantity={(qty) => onUpdateQuantity(item.itemId, qty)}
            onRemoveItem={() => onRemoveItem(item.itemId)}
          />
        ))}
      </View>

      {/* Order Summary */}
      <CartSummaryCard
        summary={cart.summary}
        onProceedToCheckout={onProceedToCheckout}
        isLoading={isUpdating}
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 20,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    padding: 24,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
  },
  header: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
    color: defaultDesignTokens.neutral.neutral900,
  },
  itemCount: {
    fontSize: 14,
    color: defaultDesignTokens.neutral.neutral500,
    fontWeight: "600",
  },
  itemsList: {
    gap: 12,
  },
});
