import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from "react-native";
import { OutfitPreviewTemplateSpecContract } from "../types";

interface OutfitPreviewTemplateProps {
  data: OutfitPreviewTemplateSpecContract;
  onEditOutfit?: () => void;
  onShopOutfit?: () => void;
  currency?: string;
  testID?: string;
}

export const OutfitPreviewTemplate: React.FC<OutfitPreviewTemplateProps> = ({
  data,
  onEditOutfit,
  onShopOutfit,
  currency = "INR",
  testID = "outfit-preview-screen",
}) => {
  const { outfit, item_count, total_price } = data;
  const filledSlots = outfit.slots.filter((s) => s.item);

  return (
    <View testID={testID} style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.styleName}>{outfit.style_name.toUpperCase()}</Text>
          <Text style={styles.title}>{outfit.name}</Text>
          <Text style={styles.itemsSummary}>
            {item_count} Pieces • {currency === "INR" ? "₹" : "$"}
            {total_price.toLocaleString()}
          </Text>
        </View>

        {/* Hero image if present */}
        {outfit.hero_image_uri && (
          <Image
            source={{ uri: outfit.hero_image_uri }}
            style={styles.heroImage}
            resizeMode="cover"
          />
        )}

        {/* Wardrobe Breakdown */}
        <View style={styles.breakdownSection}>
          <Text style={styles.sectionTitle}>WARDROBE BREAKDOWN</Text>
          {filledSlots.map((slot) => {
            if (!slot.item) return null;
            return (
              <View key={slot.id} style={styles.itemRow}>
                <Image
                  source={{ uri: slot.item.image_uri }}
                  style={styles.itemImage}
                  resizeMode="cover"
                />
                <View style={styles.itemDetails}>
                  <Text style={styles.slotCategory}>{slot.name.toUpperCase()}</Text>
                  <Text style={styles.itemTitle}>{slot.item.title}</Text>
                  <Text style={styles.itemBrand}>{slot.item.brand}</Text>
                </View>
                <Text style={styles.itemPrice}>
                  {currency === "INR" ? "₹" : "$"}
                  {slot.item.price.toLocaleString()}
                </Text>
              </View>
            );
          })}
        </View>
      </ScrollView>

      {/* Action Footer */}
      <View style={styles.footer}>
        {onEditOutfit && (
          <TouchableOpacity
            testID="edit-outfit-btn"
            style={styles.editBtn}
            onPress={onEditOutfit}
          >
            <Text style={styles.editBtnText}>Edit Outfit</Text>
          </TouchableOpacity>
        )}
        {onShopOutfit && (
          <TouchableOpacity
            testID="shop-outfit-btn"
            style={styles.shopBtn}
            onPress={onShopOutfit}
          >
            <Text style={styles.shopBtnText}>Shop Complete Look</Text>
          </TouchableOpacity>
        )}
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
  header: {
    padding: 20,
    alignItems: "center",
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  styleName: {
    fontSize: 11,
    fontWeight: "700",
    color: "#6b7280",
    letterSpacing: 1.5,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
    color: "#111111",
    marginTop: 4,
  },
  itemsSummary: {
    fontSize: 13,
    color: "#4b5563",
    marginTop: 4,
    fontWeight: "500",
  },
  heroImage: {
    width: "100%",
    height: 260,
    backgroundColor: "#f3f4f6",
  },
  breakdownSection: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
    marginBottom: 12,
  },
  itemRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
    gap: 12,
  },
  itemImage: {
    width: 56,
    height: 56,
    borderRadius: 8,
    backgroundColor: "#f3f4f6",
  },
  itemDetails: {
    flex: 1,
  },
  slotCategory: {
    fontSize: 10,
    fontWeight: "700",
    color: "#9ca3af",
  },
  itemTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111111",
    marginTop: 2,
  },
  itemBrand: {
    fontSize: 11,
    color: "#6b7280",
  },
  itemPrice: {
    fontSize: 14,
    fontWeight: "700",
    color: "#111111",
  },
  footer: {
    flexDirection: "row",
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
    backgroundColor: "#ffffff",
    gap: 10,
  },
  editBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d1d5db",
    alignItems: "center",
    justifyContent: "center",
  },
  editBtnText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#374151",
  },
  shopBtn: {
    flex: 1.5,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: "#111111",
    alignItems: "center",
    justifyContent: "center",
  },
  shopBtnText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#ffffff",
  },
});
