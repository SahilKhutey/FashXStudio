import React from "react";
import { View, Text, Pressable, StyleSheet } from "react-native";

type Props = {
  message?: string;
  onClear?: () => void;
};

export function EmptyProducts({
  message = "Try a different search or remove some filters.",
  onClear,
}: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        No products found
      </Text>
      <Text style={styles.description}>{message}</Text>
      {onClear ? (
        <Pressable accessibilityRole="button" onPress={onClear} style={styles.button}>
          <Text style={styles.action}>Clear filters</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    gap: 10,
  },
  title: { fontSize: 18, fontWeight: "700", color: "#111827" },
  description: { textAlign: "center", color: "#6B7280", fontSize: 14 },
  button: { padding: 10 },
  action: { fontWeight: "700", color: "#4F46E5" },
});
