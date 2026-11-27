import React from "react";
import { Pressable, StyleSheet, Text } from "react-native";

interface SaveProductButtonProps {
  isSaved: boolean;
  onToggle: (nextSaved: boolean) => void;
  disabled?: boolean;
}

export function SaveProductButton({
  isSaved,
  onToggle,
  disabled = false,
}: SaveProductButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: isSaved, disabled }}
      disabled={disabled}
      onPress={() => onToggle(!isSaved)}
      style={[styles.button, isSaved && styles.saved]}
    >
      <Text style={styles.label}>{isSaved ? "Saved" : "Save"}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    borderWidth: 1,
    borderColor: "#D0D5DD",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  saved: { backgroundColor: "#EEF2FF", borderColor: "#4F46E5" },
  label: { fontSize: 13, color: "#111827", fontWeight: "500" },
});
