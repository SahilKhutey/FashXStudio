import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

interface Props {
  onExplore: () => void;
}

export function EmptyCloset({ onExplore }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Your closet is empty
      </Text>
      <Text style={styles.description}>
        Save your favourite products and try-on results to keep them in one place.
      </Text>
      <Pressable onPress={onExplore} accessibilityRole="button" style={styles.button}>
        <Text style={styles.buttonText}>Explore products</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    gap: 12,
  },
  title: { fontSize: 22, fontWeight: "700", color: "#111827" },
  description: { textAlign: "center", color: "#6B7280", fontSize: 14 },
  button: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: "#111827",
    borderRadius: 10,
  },
  buttonText: { color: "#FFFFFF", fontWeight: "600" },
});
