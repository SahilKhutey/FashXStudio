import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, FlatList } from "react-native";
import { LocalProductsTemplateSpecContract } from "../types";
import { RegionalFilterChips } from "../components/RegionalFilterChips";

interface LocalProductsTemplateProps {
  data: LocalProductsTemplateSpecContract;
  activeFilter?: string;
  onSelectFilter?: (filter: string) => void;
  onPressProduct?: (productId: string) => void;
  onAddToCart?: (productId: string) => void;
  testID?: string;
}

export const LocalProductsTemplate: React.FC<LocalProductsTemplateProps> = ({
  data,
  activeFilter = "All",
  onSelectFilter,
  onPressProduct,
  onAddToCart,
  testID = "local-products-screen",
}) => {
  const { region, products, total_count, available_filters } = data;

  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.regionTag}>{region.name.toUpperCase()} CATALOGUE</Text>
        <Text style={styles.title}>Locally Crafted Pieces</Text>
        <Text style={styles.countText}>{total_count} products originating from {region.name}</Text>
      </View>

      {available_filters.length > 0 && (
        <View style={styles.filtersWrapper}>
          <RegionalFilterChips
            filters={available_filters}
            selectedFilter={activeFilter}
            onSelectFilter={(f) => onSelectFilter?.(f)}
          />
        </View>
      )}

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.grid}>
          {products.map((item) => (
            <TouchableOpacity
              key={item.id}
              testID={`local-product-card-${item.id}`}
              style={styles.card}
              onPress={() => onPressProduct?.(item.id)}
              activeOpacity={0.85}
            >
              <View style={styles.imagePlaceholder}>
                <Text style={styles.imageTag}>{item.media_type.toUpperCase()}</Text>
              </View>
              <View style={styles.cardBody}>
                <Text style={styles.cardTitle} numberOfLines={1}>
                  {item.title}
                </Text>
                {item.subtitle && (
                  <Text style={styles.cardSubtitle} numberOfLines={1}>
                    {item.subtitle}
                  </Text>
                )}
                {onAddToCart && (
                  <TouchableOpacity
                    testID={`add-to-cart-btn-${item.id}`}
                    style={styles.cartButton}
                    onPress={() => onAddToCart(item.id)}
                  >
                    <Text style={styles.cartButtonText}>+ ADD TO BAG</Text>
                  </TouchableOpacity>
                )}
              </View>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FDFDFD",
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  regionTag: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1.2,
    color: "#8E8E93",
    marginBottom: 4,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.4,
  },
  countText: {
    fontSize: 13,
    color: "#636366",
    marginTop: 4,
  },
  filtersWrapper: {
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  card: {
    width: "48%",
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    overflow: "hidden",
    marginBottom: 16,
  },
  imagePlaceholder: {
    height: 160,
    backgroundColor: "#F2F2F7",
    justifyContent: "center",
    alignItems: "center",
  },
  imageTag: {
    fontSize: 10,
    fontWeight: "700",
    color: "#AEAEB2",
    letterSpacing: 1,
  },
  cardBody: {
    padding: 10,
  },
  cardTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1C1C1E",
    marginBottom: 2,
  },
  cardSubtitle: {
    fontSize: 11,
    color: "#636366",
    marginBottom: 8,
  },
  cartButton: {
    marginTop: 6,
    backgroundColor: "#1C1C1E",
    paddingVertical: 6,
    borderRadius: 4,
    alignItems: "center",
  },
  cartButtonText: {
    color: "#FFFFFF",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
});
