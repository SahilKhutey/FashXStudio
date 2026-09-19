import React from "react";
import { StyleSheet, Text, View, ScrollView, TouchableOpacity } from "react-native";

export default function FeedScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.contextHeader}>
        <Text style={styles.contextTag}>TODAY IN BANGALORE</Text>
        <Text style={styles.contextTitle}>Breezy Evening &bull; Casual Layering</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.imagePlaceholder}>
          <Text style={styles.placeholderText}>Relaxed Cotton Overshirt</Text>
          <Text style={styles.placeholderSub}>Olive Green &bull; 280 GSM</Text>
        </View>

        <View style={styles.cardDetails}>
          <View style={styles.titleRow}>
            <Text style={styles.garmentTitle}>Relaxed Heavyweight Overshirt</Text>
            <Text style={styles.price}>₹999</Text>
          </View>
          <Text style={styles.explanation}>
            Matches your warm golden undertone and complements the straight jeans in your closet.
          </Text>

          <View style={styles.actionRow}>
            <TouchableOpacity style={styles.tryOnButton}>
              <Text style={styles.tryOnText}>Try On</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.secondaryButton}>
              <Text style={styles.secondaryText}>Save</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.secondaryButton}>
              <Text style={styles.secondaryText}>Buy</Text>
            </TouchableOpacity>
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
  contextHeader: {
    marginBottom: 20,
  },
  contextTag: {
    color: "#38BDF8",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
  },
  contextTitle: {
    color: "#F8FAFC",
    fontSize: 20,
    fontWeight: "700",
    marginTop: 4,
  },
  card: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#334155",
  },
  imagePlaceholder: {
    height: 280,
    backgroundColor: "#2E3B52",
    alignItems: "center",
    justifyContent: "center",
  },
  placeholderText: {
    color: "#F8FAFC",
    fontSize: 18,
    fontWeight: "600",
  },
  placeholderSub: {
    color: "#94A3B8",
    fontSize: 14,
    marginTop: 4,
  },
  cardDetails: {
    padding: 16,
  },
  titleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  garmentTitle: {
    color: "#F8FAFC",
    fontSize: 16,
    fontWeight: "700",
    flex: 1,
  },
  price: {
    color: "#38BDF8",
    fontSize: 18,
    fontWeight: "800",
  },
  explanation: {
    color: "#94A3B8",
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  actionRow: {
    flexDirection: "row",
    gap: 8,
  },
  tryOnButton: {
    flex: 2,
    backgroundColor: "#38BDF8",
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
  },
  tryOnText: {
    color: "#0F172A",
    fontWeight: "700",
    fontSize: 15,
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: "#334155",
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
  },
  secondaryText: {
    color: "#F8FAFC",
    fontWeight: "600",
    fontSize: 14,
  },
});
