import React from "react";
import { StyleSheet, Text, View, ScrollView, TouchableOpacity } from "react-native";

export default function ClosetScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Digitized Wardrobe</Text>
        <TouchableOpacity style={styles.addButton}>
          <Text style={styles.addButtonText}>+ Add Item</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>TOPS & OVERWEAR</Text>
        <View style={styles.grid}>
          <View style={styles.itemCard}>
            <Text style={styles.itemTitle}>Black Tee</Text>
            <Text style={styles.itemCategory}>Relaxed Fit</Text>
          </View>
          <View style={styles.itemCard}>
            <Text style={styles.itemTitle}>Beige Linen</Text>
            <Text style={styles.itemCategory}>Camp Collar</Text>
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>BOTTOMS</Text>
        <View style={styles.grid}>
          <View style={styles.itemCard}>
            <Text style={styles.itemTitle}>Blue Jeans</Text>
            <Text style={styles.itemCategory}>Straight Leg</Text>
          </View>
          <View style={styles.itemCard}>
            <Text style={styles.itemTitle}>Charcoal Chinos</Text>
            <Text style={styles.itemCategory}>Regular Fit</Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
  },
  title: {
    color: "#F8FAFC",
    fontSize: 22,
    fontWeight: "700",
  },
  addButton: {
    backgroundColor: "#38BDF8",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addButtonText: {
    color: "#0F172A",
    fontWeight: "700",
    fontSize: 14,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    color: "#94A3B8",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
    marginBottom: 12,
  },
  grid: {
    flexDirection: "row",
    gap: 12,
  },
  itemCard: {
    flex: 1,
    backgroundColor: "#1E293B",
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
    height: 100,
    justifyContent: "center",
  },
  itemTitle: {
    color: "#F8FAFC",
    fontSize: 15,
    fontWeight: "700",
  },
  itemCategory: {
    color: "#94A3B8",
    fontSize: 13,
    marginTop: 4,
  },
});
