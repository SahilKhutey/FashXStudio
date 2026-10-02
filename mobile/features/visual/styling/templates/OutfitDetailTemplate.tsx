import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from "react-native";
import { OutfitDetailTemplateSpecContract } from "../types";

interface OutfitDetailTemplateProps {
  data: OutfitDetailTemplateSpecContract;
  onPressProduct?: (productId: string) => void;
  onPressSimilarOutfit?: (outfitId: string) => void;
  onShopCompleteLook?: () => void;
  currency?: string;
  testID?: string;
}

export const OutfitDetailTemplate: React.FC<OutfitDetailTemplateProps> = ({
  data,
  onPressProduct,
  onPressSimilarOutfit,
  onShopCompleteLook,
  currency = "INR",
  testID = "outfit-detail-screen",
}) => {
  const { outfit, constituent_items, similar_outfits, availability } = data;

  return (
    <View testID={testID} style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        {/* Hero image */}
        {outfit.hero_image_uri && (
          <Image
            source={{ uri: outfit.hero_image_uri }}
            style={styles.heroImage}
            resizeMode="cover"
          />
        )}

        {/* Title & Style */}
        <View style={styles.header}>
          <Text style={styles.styleName}>{outfit.style_name.toUpperCase()}</Text>
          <Text style={styles.title}>{outfit.name}</Text>
          <Text style={styles.price}>
            {currency === "INR" ? "₹" : "$"}
            {outfit.total_price.toLocaleString()}
          </Text>
          {outfit.notes && <Text style={styles.notesText}>{outfit.notes}</Text>}
        </View>

        {/* Availability Banner */}
        <View
          style={[
            styles.availabilityBanner,
            availability.can_proceed_to_cart
              ? styles.availSuccess
              : styles.availWarning,
          ]}
        >
          <Text
            style={[
              styles.availText,
              availability.can_proceed_to_cart
                ? styles.availSuccessText
                : styles.availWarningText,
            ]}
          >
            {availability.can_proceed_to_cart
              ? `✓ All ${availability.total_items} items in this look are available in stock`
              : `⚠️ ${availability.unavailable_product_ids.length} of ${availability.total_items} items currently out of stock`}
          </Text>
        </View>

        {/* Constituent Products Rail/List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>SHOP THE PIECES ({constituent_items.length})</Text>
          {constituent_items.map((item) => (
            <TouchableOpacity
              key={item.product_id}
              testID={`piece-${item.product_id}`}
              activeOpacity={0.8}
              onPress={() => onPressProduct?.(item.product_id)}
              style={styles.pieceRow}
            >
              <Image
                source={{ uri: item.image_uri }}
                style={styles.pieceImage}
                resizeMode="cover"
              />
              <View style={styles.pieceDetails}>
                <Text style={styles.pieceBrand}>{item.brand}</Text>
                <Text style={styles.pieceTitle}>{item.title}</Text>
                <Text style={styles.piecePrice}>
                  {currency === "INR" ? "₹" : "$"}
                  {item.price.toLocaleString()}
                </Text>
              </View>
              <View style={styles.viewProductBadge}>
                <Text style={styles.viewProductText}>View</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Similar Outfits */}
        {similar_outfits.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>SIMILAR LOOKS</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.similarRail}>
              {similar_outfits.map((sim) => (
                <TouchableOpacity
                  key={sim.id}
                  testID={`similar-outfit-${sim.id}`}
                  activeOpacity={0.8}
                  onPress={() => onPressSimilarOutfit?.(sim.id)}
                  style={styles.similarCard}
                >
                  {sim.hero_image_uri && (
                    <Image
                      source={{ uri: sim.hero_image_uri }}
                      style={styles.similarImage}
                      resizeMode="cover"
                    />
                  )}
                  <View style={styles.similarInfo}>
                    <Text style={styles.similarTitle} numberOfLines={1}>
                      {sim.name}
                    </Text>
                    <Text style={styles.similarPrice}>
                      {currency === "INR" ? "₹" : "$"}
                      {sim.total_price.toLocaleString()}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}
      </ScrollView>

      {/* Sticky Bottom Cart Bar */}
      <View style={styles.bottomBar}>
        <View>
          <Text style={styles.bottomLabel}>TOTAL LOOK PRICE</Text>
          <Text style={styles.bottomPrice}>
            {currency === "INR" ? "₹" : "$"}
            {outfit.total_price.toLocaleString()}
          </Text>
        </View>
        <TouchableOpacity
          testID="shop-complete-look-btn"
          disabled={!availability.can_proceed_to_cart}
          style={[
            styles.shopButton,
            !availability.can_proceed_to_cart && styles.disabledShopBtn,
          ]}
          onPress={onShopCompleteLook}
        >
          <Text style={styles.shopButtonText}>Add Complete Look to Cart</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  content: {
    paddingBottom: 40,
  },
  heroImage: {
    width: "100%",
    height: 300,
    backgroundColor: "#f3f4f6",
  },
  header: {
    padding: 16,
  },
  styleName: {
    fontSize: 11,
    fontWeight: "700",
    color: "#6b7280",
    letterSpacing: 1,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
    color: "#111111",
    marginTop: 4,
  },
  price: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111111",
    marginTop: 4,
  },
  notesText: {
    fontSize: 13,
    color: "#555555",
    marginTop: 6,
    lineHeight: 18,
  },
  availabilityBanner: {
    marginHorizontal: 16,
    padding: 10,
    borderRadius: 8,
    marginBottom: 16,
  },
  availSuccess: {
    backgroundColor: "#ecfdf5",
  },
  availWarning: {
    backgroundColor: "#fffbeb",
  },
  availText: {
    fontSize: 12,
    fontWeight: "600",
  },
  availSuccessText: {
    color: "#065f46",
  },
  availWarningText: {
    color: "#92400e",
  },
  section: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
    marginBottom: 12,
  },
  pieceRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
    gap: 12,
  },
  pieceImage: {
    width: 60,
    height: 60,
    borderRadius: 6,
    backgroundColor: "#f3f4f6",
  },
  pieceDetails: {
    flex: 1,
  },
  pieceBrand: {
    fontSize: 10,
    fontWeight: "700",
    color: "#6b7280",
    textTransform: "uppercase",
  },
  pieceTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111111",
    marginTop: 2,
  },
  piecePrice: {
    fontSize: 13,
    fontWeight: "700",
    color: "#111111",
    marginTop: 2,
  },
  viewProductBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    backgroundColor: "#f3f4f6",
  },
  viewProductText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#374151",
  },
  similarRail: {
    gap: 12,
  },
  similarCard: {
    width: 140,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    overflow: "hidden",
  },
  similarImage: {
    width: 140,
    height: 150,
    backgroundColor: "#f3f4f6",
  },
  similarInfo: {
    padding: 8,
  },
  similarTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111111",
  },
  similarPrice: {
    fontSize: 12,
    fontWeight: "700",
    color: "#111111",
    marginTop: 2,
  },
  bottomBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
  },
  bottomLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#6b7280",
    letterSpacing: 0.5,
  },
  bottomPrice: {
    fontSize: 18,
    fontWeight: "800",
    color: "#111111",
  },
  shopButton: {
    backgroundColor: "#111111",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
  },
  disabledShopBtn: {
    backgroundColor: "#9ca3af",
  },
  shopButtonText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "700",
  },
});
