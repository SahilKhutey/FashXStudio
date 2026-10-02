import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { BreadcrumbItemContract, ProductAvailabilityState } from "../types";

interface ProductInfoProps {
  brand: string;
  title: string;
  price: number;
  originalPrice?: number | null;
  currency?: string;
  discountPercentage?: number | null;
  rating?: number;
  reviewCount?: number;
  availability?: ProductAvailabilityState;
  stockUnits?: number | null;
  shortSummary?: string;
  breadcrumbs?: BreadcrumbItemContract[];
  testID?: string;
}

export const ProductInfo: React.FC<ProductInfoProps> = ({
  brand,
  title,
  price,
  originalPrice,
  currency = "INR",
  discountPercentage,
  rating = 0,
  reviewCount = 0,
  availability = "in_stock",
  stockUnits,
  shortSummary,
  breadcrumbs = [],
  testID = "product-info",
}) => {
  const getAvailabilityColor = () => {
    switch (availability) {
      case "in_stock":
        return "#107c41";
      case "low_stock":
        return "#d83b01";
      case "out_of_stock":
      case "unavailable":
        return "#a80000";
      case "pre_order":
        return "#0078d4";
      default:
        return "#666666";
    }
  };

  const getAvailabilityLabel = () => {
    switch (availability) {
      case "in_stock":
        return "● In Stock";
      case "low_stock":
        return `● Low Stock (${stockUnits ?? "Few"} units remaining)`;
      case "out_of_stock":
        return "✕ Out of Stock";
      case "pre_order":
        return "⏳ Pre-Order";
      case "unavailable":
        return "✕ Currently Unavailable";
      default:
        return "● Check Availability";
    }
  };

  return (
    <View testID={testID} style={styles.container}>
      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <View style={styles.breadcrumbRow}>
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={`crumb-${idx}`}>
              <Text
                style={[
                  styles.breadcrumbText,
                  crumb.is_current && styles.breadcrumbCurrent,
                ]}
                numberOfLines={1}
              >
                {crumb.label}
              </Text>
              {idx < breadcrumbs.length - 1 && (
                <Text style={styles.breadcrumbSeparator}> / </Text>
              )}
            </React.Fragment>
          ))}
        </View>
      )}

      {/* Brand & Title */}
      <Text style={styles.brandText}>{brand.toUpperCase()}</Text>
      <Text style={styles.titleText}>{title}</Text>

      {/* Rating & Review Count */}
      {rating > 0 && (
        <View style={styles.ratingRow}>
          <Text style={styles.ratingStar}>★</Text>
          <Text style={styles.ratingValue}>{rating.toFixed(1)}</Text>
          {reviewCount > 0 && (
            <Text style={styles.reviewCountText}>({reviewCount} reviews)</Text>
          )}
        </View>
      )}

      {/* Price & Discount */}
      <View style={styles.priceRow}>
        <Text style={styles.currentPrice}>
          {currency === "INR" ? "₹" : "$"}
          {price.toLocaleString()}
        </Text>
        {originalPrice && originalPrice > price && (
          <Text style={styles.originalPrice}>
            {currency === "INR" ? "₹" : "$"}
            {originalPrice.toLocaleString()}
          </Text>
        )}
        {discountPercentage && discountPercentage > 0 && (
          <View style={styles.discountBadge}>
            <Text style={styles.discountText}>{discountPercentage}% OFF</Text>
          </View>
        )}
      </View>

      {/* Availability Status */}
      <View style={styles.availabilityRow}>
        <Text style={[styles.availabilityText, { color: getAvailabilityColor() }]}>
          {getAvailabilityLabel()}
        </Text>
      </View>

      {/* Short Summary */}
      {shortSummary && (
        <Text style={styles.summaryText}>{shortSummary}</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#ffffff",
  },
  breadcrumbRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
    flexWrap: "wrap",
  },
  breadcrumbText: {
    fontSize: 12,
    color: "#777777",
  },
  breadcrumbCurrent: {
    color: "#222222",
    fontWeight: "600",
  },
  breadcrumbSeparator: {
    fontSize: 12,
    color: "#aaaaaa",
  },
  brandText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#666666",
    letterSpacing: 1,
    marginBottom: 4,
  },
  titleText: {
    fontSize: 20,
    fontWeight: "700",
    color: "#111111",
    lineHeight: 26,
    marginBottom: 8,
  },
  ratingRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
    gap: 4,
  },
  ratingStar: {
    fontSize: 15,
    color: "#d97706",
  },
  ratingValue: {
    fontSize: 14,
    fontWeight: "700",
    color: "#111111",
  },
  reviewCountText: {
    fontSize: 13,
    color: "#777777",
  },
  priceRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 8,
  },
  currentPrice: {
    fontSize: 22,
    fontWeight: "800",
    color: "#111111",
  },
  originalPrice: {
    fontSize: 16,
    color: "#888888",
    textDecorationLine: "line-through",
  },
  discountBadge: {
    backgroundColor: "#e6f4ea",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  discountText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#137333",
  },
  availabilityRow: {
    marginBottom: 10,
  },
  availabilityText: {
    fontSize: 13,
    fontWeight: "600",
  },
  summaryText: {
    fontSize: 14,
    color: "#444444",
    lineHeight: 20,
  },
});
