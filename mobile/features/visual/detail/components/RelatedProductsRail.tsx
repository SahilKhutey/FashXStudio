import React from "react";
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from "react-native";
import { RelatedProductItemContract, RelatedItemRelationship } from "../types";

interface RelatedProductsRailProps {
  title: string;
  relationship: RelatedItemRelationship;
  items: RelatedProductItemContract[];
  onSelectProduct?: (productId: string) => void;
  testID?: string;
}

export const RelatedProductsRail: React.FC<RelatedProductsRailProps> = ({
  title,
  relationship,
  items = [],
  onSelectProduct,
  testID = "related-products-rail",
}) => {
  if (items.length === 0) return null;

  const getRelationshipBadge = () => {
    switch (relationship) {
      case "similar":
        return "Similar Aesthetic";
      case "recommended":
        return "AI Match";
      case "styled_with":
        return "Complete Ensemble";
      default:
        return null;
    }
  };

  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.titleText}>{title}</Text>
        {getRelationshipBadge() && (
          <View style={styles.typeBadge}>
            <Text style={styles.typeBadgeText}>{getRelationshipBadge()}</Text>
          </View>
        )}
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {items.map((item) => (
          <TouchableOpacity
            key={item.product_id}
            testID={`${testID}-item-${item.product_id}`}
            onPress={() => onSelectProduct && onSelectProduct(item.product_id)}
            style={styles.cardWrapper}
            accessibilityRole="button"
            accessibilityLabel={`${item.title} by ${item.brand}, ₹${item.price}`}
          >
            <View style={styles.imageWrapper}>
              <Image
                source={{ uri: item.image_uri }}
                style={styles.cardImage}
                resizeMode="cover"
              />
            </View>

            <View style={styles.cardContent}>
              <Text style={styles.brandText} numberOfLines={1}>
                {item.brand}
              </Text>
              <Text style={styles.productTitle} numberOfLines={2}>
                {item.title}
              </Text>

              <View style={styles.priceRow}>
                <Text style={styles.priceText}>₹{item.price.toLocaleString()}</Text>
                {item.original_price && item.original_price > item.price && (
                  <Text style={styles.originalPriceText}>
                    ₹{item.original_price.toLocaleString()}
                  </Text>
                )}
              </View>

              {/* Explainable recommendation reason (Section 9.25, 9.46) */}
              {item.reason && (
                <Text style={styles.reasonText} numberOfLines={2}>
                  ℹ {item.reason}
                </Text>
              )}
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
    backgroundColor: "#ffffff",
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  titleText: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
  },
  typeBadge: {
    backgroundColor: "#f0f4f8",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  typeBadgeText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#2b6cb0",
  },
  scrollContent: {
    paddingHorizontal: 16,
    gap: 12,
  },
  cardWrapper: {
    width: 140,
    backgroundColor: "#ffffff",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#eeeeee",
    overflow: "hidden",
  },
  imageWrapper: {
    width: "100%",
    aspectRatio: 3 / 4,
    backgroundColor: "#f5f5f5",
  },
  cardImage: {
    width: "100%",
    height: "100%",
  },
  cardContent: {
    padding: 8,
  },
  brandText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#666666",
    marginBottom: 2,
  },
  productTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111111",
    lineHeight: 16,
    marginBottom: 6,
  },
  priceRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  priceText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#111111",
  },
  originalPriceText: {
    fontSize: 11,
    color: "#888888",
    textDecorationLine: "line-through",
  },
  reasonText: {
    fontSize: 10,
    color: "#4a5568",
    marginTop: 4,
    fontStyle: "italic",
    lineHeight: 13,
  },
});
