import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from "react-native";
import { LookBuilderTemplateSpecContract } from "../types";

interface LookBuilderTemplateProps {
  data: LookBuilderTemplateSpecContract;
  onAddItem?: () => void;
  onSaveLook?: () => void;
  currency?: string;
  testID?: string;
}

export const LookBuilderTemplate: React.FC<LookBuilderTemplateProps> = ({
  data,
  onAddItem,
  onSaveLook,
  currency = "INR",
  testID = "look-builder-screen",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{data.title}</Text>
        <Text style={styles.narrative}>{data.context_narrative}</Text>
        <View style={styles.tagsRow}>
          {data.style_tags.map((tag) => (
            <View key={tag} style={styles.tagBadge}>
              <Text style={styles.tagText}>#{tag}</Text>
            </View>
          ))}
        </View>
      </View>

      <ScrollView
        style={styles.itemsList}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.sectionTitle}>MOODBOARD & CURATED PIECES</Text>
        <View style={styles.grid}>
          {data.visual_items.map((item, idx) => (
            <View key={`${item.product_id}-${idx}`} style={styles.card}>
              <Image source={{ uri: item.image_uri }} style={styles.image} resizeMode="cover" />
              <View style={styles.cardDetails}>
                <Text style={styles.brand}>{item.brand}</Text>
                <Text style={styles.itemTitle} numberOfLines={1}>{item.title}</Text>
                <Text style={styles.price}>
                  {currency === "INR" ? "₹" : "$"}
                  {item.price.toLocaleString()}
                </Text>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        {onAddItem && (
          <TouchableOpacity
            testID="look-builder-add-btn"
            style={styles.secondaryBtn}
            onPress={onAddItem}
          >
            <Text style={styles.secondaryBtnText}>+ Add Piece</Text>
          </TouchableOpacity>
        )}
        {onSaveLook && (
          <TouchableOpacity
            testID="look-builder-save-btn"
            style={styles.primaryBtn}
            onPress={onSaveLook}
          >
            <Text style={styles.primaryBtnText}>Publish Look</Text>
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
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: "#111111",
  },
  narrative: {
    fontSize: 13,
    color: "#4b5563",
    marginTop: 4,
    lineHeight: 18,
  },
  tagsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginTop: 8,
  },
  tagBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: "#f3f4f6",
    borderRadius: 4,
  },
  tagText: {
    fontSize: 11,
    color: "#374151",
    fontWeight: "600",
  },
  itemsList: {
    flex: 1,
  },
  listContent: {
    padding: 16,
    paddingBottom: 32,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
    marginBottom: 12,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  card: {
    width: "48%",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    overflow: "hidden",
  },
  image: {
    width: "100%",
    height: 150,
    backgroundColor: "#f3f4f6",
  },
  cardDetails: {
    padding: 8,
  },
  brand: {
    fontSize: 10,
    fontWeight: "700",
    color: "#6b7280",
  },
  itemTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111111",
    marginTop: 2,
  },
  price: {
    fontSize: 12,
    fontWeight: "700",
    color: "#111111",
    marginTop: 2,
  },
  footer: {
    flexDirection: "row",
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
    gap: 10,
  },
  secondaryBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d1d5db",
    alignItems: "center",
  },
  secondaryBtnText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#374151",
  },
  primaryBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: "#111111",
    alignItems: "center",
  },
  primaryBtnText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#ffffff",
  },
});
