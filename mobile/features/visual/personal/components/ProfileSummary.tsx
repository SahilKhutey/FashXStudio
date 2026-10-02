import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { SavedSummaryContract } from "../types";

interface ProfileSummaryProps {
  summary: SavedSummaryContract;
  onSelectCategory?: (category: string) => void;
  testID?: string;
}

export const ProfileSummary: React.FC<ProfileSummaryProps> = ({
  summary,
  onSelectCategory,
  testID = "profile-summary",
}) => {
  const items = [
    { key: "products", label: "Products", count: summary.products_count },
    { key: "looks", label: "Looks", count: summary.looks_count },
    { key: "fashion", label: "Fashion", count: summary.fashion_count },
    { key: "wishlist", label: "Wishlist", count: summary.wishlist_count },
    { key: "collections", label: "Collections", count: summary.collections_count },
  ];

  return (
    <View testID={testID} style={styles.container}>
      <Text style={styles.sectionTitle}>SAVED OVERVIEW</Text>
      <View style={styles.grid}>
        {items.map((item) => (
          <TouchableOpacity
            key={item.key}
            testID={`summary-item-${item.key}`}
            style={styles.card}
            onPress={() => onSelectCategory && onSelectCategory(item.key)}
            accessibilityRole="button"
            accessibilityLabel={`${item.label}, ${item.count} items`}
          >
            <Text style={styles.count}>{item.count}</Text>
            <Text style={styles.label}>{item.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  card: {
    width: "18%",
    alignItems: "center",
    paddingVertical: 10,
    backgroundColor: "#F2F2F7",
    borderRadius: 8,
  },
  count: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 2,
  },
  label: {
    fontSize: 10,
    fontWeight: "500",
    color: "#636366",
  },
});
