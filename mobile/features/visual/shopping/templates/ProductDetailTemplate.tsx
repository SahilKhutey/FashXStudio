/**
 * ProductDetailTemplate Component — Phase 07 (Section 7.21 - 7.23, 7.59).
 *
 * Full-screen product detail layout with:
 * - Breadcrumbs
 * - 3:4 Media Gallery
 * - Brand, Title, Rating, Price, Availability
 * - Variant Selector
 * - Delivery Information & Specifications
 * - Sticky Bottom Purchase Bar (Section 7.59)
 */

import React, { useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { ProductDetailTemplateSpec } from "../types";
import { ProductGallery } from "../product/ProductGallery";
import { VariantSelector } from "../product/VariantSelector";
import { AvailabilityBadge } from "../product/AvailabilityBadge";
import { Price } from "../../components/Price";
import { Rating } from "../../components/Rating";
import { Button } from "../../components/Button";

export interface ProductDetailTemplateProps {
  spec: ProductDetailTemplateSpec;
  onAddToCart: (selectedVariants: Record<string, string>) => void;
  onToggleWishlist: () => void;
  isAddingToCart?: boolean;
}

export const ProductDetailTemplate: React.FC<ProductDetailTemplateProps> = ({
  spec,
  onAddToCart,
  onToggleWishlist,
  isAddingToCart,
}) => {
  const { product, breadcrumbTrail, stickyActionEnabled } = spec;

  // Initialize selected variants
  const initialVariants: Record<string, string> = {};
  product.variantGroups.forEach((group) => {
    const defaultOption = group.options.find((o) => o.state === "selected") || group.options[0];
    if (defaultOption) {
      initialVariants[group.variantType] = defaultOption.value;
    }
  });

  const [selectedVariants, setSelectedVariants] = useState<Record<string, string>>(initialVariants);

  const handleSelectVariant = (groupType: string, optionValue: string) => {
    setSelectedVariants((prev) => ({
      ...prev,
      [groupType]: optionValue,
    }));
  };

  const isOutOfStock = product.availability === "out_of_stock";

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Breadcrumbs */}
        {breadcrumbTrail.length > 0 ? (
          <Text style={styles.breadcrumbs}>{breadcrumbTrail.join(" / ")}</Text>
        ) : null}

        {/* 3:4 Media Gallery */}
        <ProductGallery mediaGallery={product.mediaGallery} />

        {/* Product Information */}
        <View style={styles.infoSection}>
          <View style={styles.brandRow}>
            <Text style={styles.brand}>{product.brand}</Text>
            <AvailabilityBadge availability={product.availability} stockCount={product.stockCount} />
          </View>

          <Text style={styles.title}>{product.title}</Text>

          {product.rating ? (
            <Rating
              value={product.rating.value}
              ratingCount={product.rating.ratingCount}
              showCount
              size="sm"
            />
          ) : null}

          <Price spec={product.price} size="lg" />

          <Text style={styles.description}>{product.description}</Text>
        </View>

        {/* Variant Selectors */}
        {product.variantGroups.length > 0 ? (
          <View style={styles.section}>
            <VariantSelector
              groups={product.variantGroups}
              selectedVariants={selectedVariants}
              onSelectVariant={handleSelectVariant}
            />
          </View>
        ) : null}

        {/* Delivery Info */}
        {product.deliveryInfo ? (
          <View style={styles.deliveryCard}>
            <Text style={styles.deliveryTitle}>🚚 Delivery Information</Text>
            <Text style={styles.deliveryText}>
              Estimated delivery: {product.deliveryInfo.estimatedDeliveryDays}
            </Text>
            <Text style={styles.deliveryFee}>
              {product.deliveryInfo.isFreeDelivery
                ? "Eligible for FREE Express Delivery"
                : `Shipping Fee: ₹${product.deliveryInfo.shippingFee}`}
            </Text>
          </View>
        ) : null}

        {/* Specifications */}
        {product.specifications.length > 0 ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Specifications</Text>
            <View style={styles.specsTable}>
              {product.specifications.map((specItem, idx) => (
                <View key={idx} style={styles.specRow}>
                  <Text style={styles.specName}>{specItem.name}</Text>
                  <Text style={styles.specValue}>{specItem.value}</Text>
                </View>
              ))}
            </View>
          </View>
        ) : null}
      </ScrollView>

      {/* Sticky Bottom Purchase Bar (Section 7.59) */}
      {stickyActionEnabled ? (
        <View style={styles.stickyBar}>
          <View style={styles.stickyPriceContainer}>
            <Text style={styles.stickyPriceLabel}>Total Price</Text>
            <Text style={styles.stickyPrice}>
              {product.price.currency_symbol || "₹"}
              {product.price.amount.toLocaleString()}
            </Text>
          </View>

          <View style={styles.stickyActions}>
            <Button
              label={product.isInWishlist ? "Saved" : "Save"}
              variant="outline"
              size="md"
              onPress={onToggleWishlist}
            />
            <Button
              label={isOutOfStock ? "Out of Stock" : "Add to Cart"}
              variant="primary"
              size="md"
              disabled={isOutOfStock}
              loading={isAddingToCart}
              onPress={() => onAddToCart(selectedVariants)}
            />
          </View>
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 100,
    gap: 16,
  },
  breadcrumbs: {
    fontSize: 12,
    color: defaultDesignTokens.neutral.neutral500,
    marginBottom: 4,
  },
  infoSection: {
    gap: 8,
  },
  brandRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  brand: {
    fontSize: 12,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral600,
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: defaultDesignTokens.neutral.neutral900,
    lineHeight: 26,
  },
  description: {
    fontSize: 14,
    color: defaultDesignTokens.neutral.neutral700,
    lineHeight: 20,
    marginTop: 4,
  },
  section: {
    borderTopWidth: 1,
    borderTopColor: defaultDesignTokens.neutral.neutral200,
    paddingTop: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  specsTable: {
    gap: 6,
  },
  specRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 4,
  },
  specName: {
    fontSize: 13,
    color: defaultDesignTokens.neutral.neutral500,
  },
  specValue: {
    fontSize: 13,
    fontWeight: "600",
    color: defaultDesignTokens.neutral.neutral800,
  },
  deliveryCard: {
    padding: 14,
    borderRadius: 8,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    gap: 4,
  },
  deliveryTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
  },
  deliveryText: {
    fontSize: 13,
    color: defaultDesignTokens.neutral.neutral700,
  },
  deliveryFee: {
    fontSize: 12,
    fontWeight: "600",
    color: defaultDesignTokens.status.success,
  },
  stickyBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
    borderTopWidth: 1,
    borderTopColor: defaultDesignTokens.neutral.neutral200,
  },
  stickyPriceContainer: {
    gap: 2,
  },
  stickyPriceLabel: {
    fontSize: 11,
    color: defaultDesignTokens.neutral.neutral500,
  },
  stickyPrice: {
    fontSize: 18,
    fontWeight: "800",
    color: defaultDesignTokens.neutral.neutral900,
  },
  stickyActions: {
    flexDirection: "row",
    gap: 8,
  },
});
