import React, { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from "react-native";
import { ProductAvailabilityState } from "../types";

interface ProductActionsProps {
  price: number;
  currency?: string;
  availability?: ProductAvailabilityState;
  isWishlisted?: boolean;
  onAddToCart: () => void;
  onBuyNow?: () => void;
  onToggleWishlist?: () => void;
  isAddingToCart?: boolean;
  isSticky?: boolean;
  testID?: string;
}

export const ProductActions: React.FC<ProductActionsProps> = ({
  price,
  currency = "INR",
  availability = "in_stock",
  isWishlisted = false,
  onAddToCart,
  onBuyNow,
  onToggleWishlist,
  isAddingToCart = false,
  isSticky = false,
  testID = "product-actions",
}) => {
  const [localWishlisted, setLocalWishlisted] = useState(isWishlisted);
  const isOutOfStock = availability === "out_of_stock" || availability === "unavailable";

  const handleWishlistPress = () => {
    setLocalWishlisted(!localWishlisted);
    if (onToggleWishlist) onToggleWishlist();
  };

  return (
    <View
      testID={testID}
      style={[styles.container, isSticky && styles.stickyContainer]}
    >
      {/* Price tag visible in sticky mode on smaller viewports */}
      {isSticky && (
        <View style={styles.stickyPriceWrapper}>
          <Text style={styles.stickyPriceLabel}>Total</Text>
          <Text style={styles.stickyPriceValue}>
            {currency === "INR" ? "₹" : "$"}
            {price.toLocaleString()}
          </Text>
        </View>
      )}

      {/* Wishlist Button */}
      {onToggleWishlist && (
        <TouchableOpacity
          testID={`${testID}-wishlist-button`}
          onPress={handleWishlistPress}
          style={[
            styles.wishlistButton,
            localWishlisted && styles.wishlistButtonActive,
          ]}
          accessibilityRole="button"
          accessibilityLabel={localWishlisted ? "Remove from wishlist" : "Add to wishlist"}
        >
          <Text style={[styles.wishlistIcon, localWishlisted && styles.wishlistIconActive]}>
            {localWishlisted ? "♥" : "♡"}
          </Text>
        </TouchableOpacity>
      )}

      {/* Add to Cart Button */}
      <TouchableOpacity
        testID={`${testID}-add-to-cart`}
        disabled={isOutOfStock || isAddingToCart}
        onPress={onAddToCart}
        style={[
          styles.addToCartButton,
          isOutOfStock && styles.actionButtonDisabled,
        ]}
        accessibilityRole="button"
        accessibilityLabel={isOutOfStock ? "Out of Stock" : "Add to Cart"}
      >
        {isAddingToCart ? (
          <ActivityIndicator color="#ffffff" size="small" />
        ) : (
          <Text style={styles.addToCartText}>
            {isOutOfStock ? "Out of Stock" : "Add to Cart"}
          </Text>
        )}
      </TouchableOpacity>

      {/* Buy Now Button */}
      {onBuyNow && !isOutOfStock && (
        <TouchableOpacity
          testID={`${testID}-buy-now`}
          onPress={onBuyNow}
          style={styles.buyNowButton}
          accessibilityRole="button"
          accessibilityLabel="Buy Now"
        >
          <Text style={styles.buyNowText}>Buy Now</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
  },
  stickyContainer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    shadowColor: "#000000",
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 8,
    paddingBottom: 20, // safe area padding for home indicator
  },
  stickyPriceWrapper: {
    marginRight: 6,
  },
  stickyPriceLabel: {
    fontSize: 11,
    color: "#777777",
  },
  stickyPriceValue: {
    fontSize: 18,
    fontWeight: "800",
    color: "#111111",
  },
  wishlistButton: {
    width: 46,
    height: 46,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: "#dddddd",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#ffffff",
  },
  wishlistButtonActive: {
    borderColor: "#e53e3e",
    backgroundColor: "#fff5f5",
  },
  wishlistIcon: {
    fontSize: 22,
    color: "#444444",
  },
  wishlistIconActive: {
    color: "#e53e3e",
  },
  addToCartButton: {
    flex: 1,
    height: 46,
    borderRadius: 8,
    backgroundColor: "#111111",
    justifyContent: "center",
    alignItems: "center",
  },
  buyNowButton: {
    flex: 1,
    height: 46,
    borderRadius: 8,
    backgroundColor: "#1a56db",
    justifyContent: "center",
    alignItems: "center",
  },
  actionButtonDisabled: {
    backgroundColor: "#cccccc",
  },
  addToCartText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
  },
  buyNowText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
  },
});
