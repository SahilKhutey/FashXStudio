import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { SavedProductsTemplateSpecContract } from "../types";
import { SavedProductCard } from "../components/SavedProductCard";

interface SavedProductsTemplateProps {
  data: SavedProductsTemplateSpecContract;
  onFilterChange?: (filter: string | null) => void;
  onSortChange?: (sort: string) => void;
  onViewProduct?: (productId: string) => void;
  onRemoveProduct?: (productId: string) => void;
  onExploreProducts?: () => void;
  testID?: string;
}

export const SavedProductsTemplate: React.FC<SavedProductsTemplateProps> = ({
  data,
  onFilterChange,
  onSortChange,
  onViewProduct,
  onRemoveProduct,
  onExploreProducts,
  testID = "saved-products-pr03",
}) => {
  const sortOptions = [
    { key: "recently_saved", label: "Recent" },
    { key: "price_asc", label: "Price: Low to High" },
    { key: "price_desc", label: "Price: High to Low" },
  ];

  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Saved Products ({data.total_count})</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.sortBar}>
          {sortOptions.map((opt) => (
            <TouchableOpacity
              key={opt.key}
              testID={`sort-opt-${opt.key}`}
              style={[styles.sortChip, data.active_sort === opt.key && styles.activeSortChip]}
              onPress={() => onSortChange && onSortChange(opt.key)}
            >
              <Text
                style={[styles.sortText, data.active_sort === opt.key && styles.activeSortText]}
              >
                {opt.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {data.items.length === 0 ? (
        <View testID="empty-saved-products" style={styles.emptyState}>
          <Text style={styles.emptyTitle}>No saved products yet.</Text>
          <Text style={styles.emptySubtitle}>
            When you find something you like, save it here.
          </Text>
          <TouchableOpacity
            testID="explore-products-button"
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
          {data.items.map((prod) => (
            <SavedProductCard
              key={prod.id}
              product={prod}
              onView={onViewProduct}
              onRemove={onRemoveProduct}
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
    marginBottom: 8,
  },
  sortBar: {
    flexDirection: "row",
  },
  sortChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: "#F2F2F7",
    marginRight: 8,
  },
  activeSortChip: {
    backgroundColor: "#1C1C1E",
  },
  sortText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#636366",
  },
  activeSortText: {
    color: "#FFFFFF",
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
    marginBottom: 6,
  },
  emptySubtitle: {
    fontSize: 13,
    color: "#636366",
    textAlign: "center",
    marginBottom: 20,
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
