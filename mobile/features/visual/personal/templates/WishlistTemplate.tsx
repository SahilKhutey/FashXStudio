import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { WishlistTemplateSpecContract } from "../types";
import { WishlistItem } from "../components/WishlistItem";

interface WishlistTemplateProps {
  data: WishlistTemplateSpecContract;
  onAddToCart?: (productId: string) => void;
  onViewAlternatives?: (altId: string) => void;
  onRemoveItem?: (id: string) => void;
  onExploreProducts?: () => void;
  testID?: string;
}

export const WishlistTemplate: React.FC<WishlistTemplateProps> = ({
  data,
  onAddToCart,
  onViewAlternatives,
  onRemoveItem,
  onExploreProducts,
  testID = "wishlist-pr06",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Wishlist ({data.total_count})</Text>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryText}>
            {data.available_count} Available • {data.unavailable_count} Out of Stock
          </Text>
        </View>
      </View>

      {data.items.length === 0 ? (
        <View testID="empty-wishlist" style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Your wishlist is empty.</Text>
          <TouchableOpacity
            testID="explore-products-btn"
            style={styles.exploreBtn}
            onPress={onExploreProducts}
            accessibilityRole="button"
            accessibilityLabel="Explore Products"
          >
            <Text style={styles.exploreBtnText}>Explore Products</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.list}>
          {data.items.map((item) => (
            <WishlistItem
              key={item.id}
              item={item}
              onAddToCart={onAddToCart}
              onViewAlternatives={onViewAlternatives}
              onRemove={onRemoveItem}
            />
          ))}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F2F2F7",
  },
  header: {
    padding: 16,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 4,
  },
  summaryRow: {
    flexDirection: "row",
  },
  summaryText: {
    fontSize: 12,
    color: "#8E8E93",
    fontWeight: "500",
  },
  list: {
    padding: 16,
  },
  emptyState: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 16,
  },
  exploreBtn: {
    backgroundColor: "#1C1C1E",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  exploreBtnText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
});
