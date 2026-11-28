import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

interface Props {
  onCreateLook?: () => void;
}

export function EmptyLooks({ onCreateLook }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        No saved looks yet
      </Text>
      <Text style={styles.description}>
        Combine items from your closet to create your first look.
      </Text>
      {onCreateLook ? (
        <Pressable
          onPress={onCreateLook}
          accessibilityRole="button"
          style={styles.button}
        >
          <Text style={styles.buttonText}>Create a look</Text>
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
