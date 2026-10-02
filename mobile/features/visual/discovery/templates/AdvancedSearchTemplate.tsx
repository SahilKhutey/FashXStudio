/**
 * AdvancedSearchTemplate Component — Phase 08 (Section 8.25).
 *
 * S09 Structured multi-criteria query builder:
 * Keywords, Category, Brand, Price Range, Color, Size, Region.
 */

import React, { useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { AdvancedSearchCriteria, AdvancedSearchTemplateSpec } from "../types";
import { Input } from "../../components/Input";
import { Button } from "../../components/Button";
import { ProductCard } from "../fashion/product/ProductCard";

export interface AdvancedSearchTemplateProps {
  spec: AdvancedSearchTemplateSpec;
  onApplySearch: (criteria: AdvancedSearchCriteria) => void;
  isSearching?: boolean;
}

export const AdvancedSearchTemplate: React.FC<AdvancedSearchTemplateProps> = ({
  spec,
  onApplySearch,
  isSearching,
}) => {
  const [keywords, setKeywords] = useState<string>(spec.criteria.keywords || "");
  const [brand, setBrand] = useState<string>(spec.criteria.brand || "");
  const [priceMax, setPriceMax] = useState<string>(
    spec.criteria.priceMax ? String(spec.criteria.priceMax) : ""
  );

  const handleApply = () => {
    onApplySearch({
      keywords: keywords.trim() || undefined,
      brand: brand.trim() || undefined,
      priceMax: priceMax ? parseFloat(priceMax) : undefined,
    });
  };

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>Advanced Search</Text>
      <Text style={styles.subtitle}>
        Refine your search with precision across categories, brands, and price parameters.
      </Text>

      {/* Form Fields */}
      <View style={styles.formSection}>
        <Input
          label="Keywords / Garment"
          value={keywords}
          placeholder="e.g. Selvedge denim jacket"
          onChangeText={setKeywords}
        />

        <Input
          label="Designer / Merchant Brand"
          value={brand}
          placeholder="e.g. RawDenim Co."
          onChangeText={setBrand}
        />

        <Input
          label="Maximum Price (₹)"
          value={priceMax}
          placeholder="e.g. 5000"
          keyboardType="numeric"
          onChangeText={setPriceMax}
        />

        <Button
          label="Apply Search Criteria"
          variant="primary"
          size="lg"
          fullWidth
          loading={isSearching}
          onPress={handleApply}
        />
      </View>

      {/* Results Preview */}
      {spec.previewResults.length > 0 ? (
        <View style={styles.previewSection}>
          <Text style={styles.previewTitle}>
            Matching Results ({spec.previewTotal})
          </Text>

          <View style={styles.grid}>
            {spec.previewResults.map((item) => (
              <View key={item.id} style={styles.gridItem}>
                <ProductCard
                  product={{
                    id: item.id,
                    brand: item.subtitle || "Brand",
                    title: item.title,
                    primaryImageUri: item.media_uri,
                    price: item.price || { amount: 2499.0 },
                    rating: item.rating,
                    category: item.category_label,
                    isSaved: item.is_saved,
                    badge: item.labels[0],
                  }}
                  onPress={() => {}}
                  onWishlistToggle={() => {}}
                />
              </View>
            ))}
          </View>
        </View>
      ) : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 20,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
    color: defaultDesignTokens.neutral.neutral900,
  },
  subtitle: {
    fontSize: 14,
    color: defaultDesignTokens.neutral.neutral600,
    lineHeight: 20,
  },
  formSection: {
    gap: 14,
    padding: 16,
    borderRadius: 12,
    backgroundColor: defaultDesignTokens.neutral.neutral50,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
  },
  previewSection: {
    gap: 12,
    marginTop: 8,
  },
  previewTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: 12,
  },
  gridItem: {
    width: "48%",
  },
});
