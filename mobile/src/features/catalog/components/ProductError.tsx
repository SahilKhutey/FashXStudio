import React from "react";
import { View, Text, Pressable, StyleSheet } from "react-native";

type Props = {
  onRetry: () => void;
};

export function ProductError({ onRetry }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Couldn&apos;t load products
      </Text>
      <Text style={styles.description}>
        Check your connection and try again.
      </Text>
      <Pressable
        accessibilityRole="button"
        onPress={onRetry}
        style={styles.button}
      >
        <Text style={styles.buttonText}>Try again</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    gap: 12,
  },
  title: { fontSize: 18, fontWeight: "700", color: "#111827" },
  description: { color: "#6B7280", textAlign: "center", fontSize: 14 },
  button: {
    paddingHorizontal: 22,
    paddingVertical: 12,
    backgroundColor: "#111827",
    borderRadius: 10,
  },
  buttonText: { color: "#FFF", fontWeight: "700" },
});
