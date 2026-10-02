import React, { useState } from "react";
import { View, StyleSheet, ScrollView, SafeAreaView } from "react-native";
import { ComprehensiveProductDetailTemplateSpecContract } from "../types";
import { ProductGallery } from "../components/ProductGallery";
import { ProductInfo } from "../components/ProductInfo";
import { VariantSelector } from "../components/VariantSelector";
import { QuantitySelector } from "../components/QuantitySelector";
import { ProductActions } from "../components/ProductActions";
import { ProductSpecifications } from "../components/ProductSpecifications";
import { ProductReviews } from "../components/ProductReviews";
import { RelatedProductsRail } from "../components/RelatedProductsRail";

interface ProductDetailTemplateProps {
  spec: ComprehensiveProductDetailTemplateSpecContract;
  onAddToCart?: (productId: string, quantity: number, variants: Record<string, string>) => void;
  onBuyNow?: (productId: string, quantity: number, variants: Record<string, string>) => void;
  onToggleWishlist?: (productId: string) => void;
  onSelectRelatedProduct?: (productId: string) => void;
  testID?: string;
}

export const ProductDetailTemplate: React.FC<ProductDetailTemplateProps> = ({
  spec,
  onAddToCart,
  onBuyNow,
  onToggleWishlist,
  onSelectRelatedProduct,
  testID = "product-detail-template",
}) => {
  const { view_model } = spec;
  const [quantity, setQuantity] = useState(1);
  const [selectedVariants, setSelectedVariants] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    view_model.variant_groups.forEach((g) => {
      if (g.selected_option_id) initial[g.group_id] = g.selected_option_id;
    });
    return initial;
  });

  const handleSelectVariant = (groupId: string, optionId: string) => {
    setSelectedVariants((prev) => ({ ...prev, [groupId]: optionId }));
  };

  const handleAddToCart = () => {
    if (onAddToCart) {
      onAddToCart(view_model.id, quantity, selectedVariants);
    }
  };

  const handleBuyNow = () => {
    if (onBuyNow) {
      onBuyNow(view_model.id, quantity, selectedVariants);
    }
  };

  return (
    <SafeAreaView testID={testID} style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Gallery */}
        <ProductGallery gallery={view_model.gallery} />

        {/* Product Information */}
        <ProductInfo
          brand={view_model.brand}
          title={view_model.title}
          price={view_model.price}
          originalPrice={view_model.original_price}
          currency={view_model.currency}
          discountPercentage={view_model.discount_percentage}
          rating={view_model.rating}
          reviewCount={view_model.review_count}
          availability={view_model.availability}
          stockUnits={view_model.stock_units}
          shortSummary={view_model.short_summary}
          breadcrumbs={view_model.breadcrumbs}
        />

        {/* Variant Selection */}
        <VariantSelector
          groups={view_model.variant_groups}
          selectedVariants={selectedVariants}
          onSelectOption={handleSelectVariant}
        />

        {/* Quantity Selection */}
        <QuantitySelector
          quantity={quantity}
          onChangeQuantity={setQuantity}
          disabled={view_model.availability === "out_of_stock"}
        />

        {/* In-Flow Product Actions */}
        <ProductActions
          price={view_model.price * quantity}
          currency={view_model.currency}
          availability={view_model.availability}
          onAddToCart={handleAddToCart}
          onBuyNow={handleBuyNow}
          onToggleWishlist={() => onToggleWishlist && onToggleWishlist(view_model.id)}
        />

        {/* Specifications & Craft */}
        <ProductSpecifications
          description={view_model.description}
          specifications={view_model.specifications}
        />

        {/* Customer Reviews */}
        <ProductReviews reviewsData={view_model.reviews} />

        {/* Styled With Ensembles */}
        {view_model.styled_with.length > 0 && (
          <RelatedProductsRail
            title="Styled With"
            relationship="styled_with"
            items={view_model.styled_with}
            onSelectProduct={onSelectRelatedProduct}
          />
        )}

        {/* Similar Products */}
        {view_model.similar_products.length > 0 && (
          <RelatedProductsRail
            title="Similar Pieces"
            relationship="similar"
            items={view_model.similar_products}
            onSelectProduct={onSelectRelatedProduct}
          />
        )}

        {/* Recommended for You */}
        {view_model.recommended_products.length > 0 && (
          <RelatedProductsRail
            title="Recommended For You"
            relationship="recommended"
            items={view_model.recommended_products}
            onSelectProduct={onSelectRelatedProduct}
          />
        )}
      </ScrollView>

      {/* Sticky Bottom Actions on Mobile (Section 9.17) */}
      <ProductActions
        isSticky
        price={view_model.price * quantity}
        currency={view_model.currency}
        availability={view_model.availability}
        onAddToCart={handleAddToCart}
        onToggleWishlist={() => onToggleWishlist && onToggleWishlist(view_model.id)}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  scrollContent: {
    paddingBottom: 90, // room for sticky purchase action bar
  },
});
