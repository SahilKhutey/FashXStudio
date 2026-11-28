import React from "react";
import { View, Text, StyleSheet } from "react-native";

const INSTRUCTIONS = [
  "Stand facing the camera.",
  "Keep your full body visible where the garment category requires it.",
  "Use clear, even lighting.",
  "Avoid mirrors, heavy shadows and strong backlighting.",
  "Keep your arms slightly away from your body.",
  "Wear clothing that makes your body outline reasonably visible.",
  "Avoid other people appearing in the photograph.",
  "Use a clear, unfiltered image.",
];

export function PhotoInstructions() {
  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Prepare your photo
      </Text>
      <Text style={styles.description}>
        A clear photo helps us generate a better virtual try-on representation.
      </Text>
      {INSTRUCTIONS.map((instruction, index) => (
        <View key={instruction} style={styles.item}>
          <Text style={styles.number}>{index + 1}.</Text>
          <Text style={styles.text}>{instruction}</Text>
        </View>
      ))}
      <Text style={styles.note}>
        Photo suitability depends on the garment category. We will validate your photo before starting the try-on.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, gap: 12 },
  title: { fontSize: 24, fontWeight: "700", color: "#111827" },
  description: { fontSize: 15, lineHeight: 22, color: "#374151" },
  item: { flexDirection: "row", gap: 10 },
  number: { fontWeight: "700", color: "#111827" },
  text: { flex: 1, lineHeight: 21, color: "#374151" },
  note: { marginTop: 8, fontSize: 13, lineHeight: 19, color: "#6B7280" },
});
