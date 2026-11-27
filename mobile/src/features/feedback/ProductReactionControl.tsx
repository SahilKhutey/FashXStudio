import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import type { ReactionState } from "./eventTypes";

interface ProductReactionControlProps {
  reaction: ReactionState;
  onChange: (nextReaction: ReactionState) => void;
  disabled?: boolean;
}

export function ProductReactionControl({
  reaction,
  onChange,
  disabled = false,
}: ProductReactionControlProps) {
  return (
    <View style={styles.row}>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ selected: reaction === "LIKE", disabled }}
        disabled={disabled}
        onPress={() => onChange(reaction === "LIKE" ? "NONE" : "LIKE")}
        style={[styles.button, reaction === "LIKE" && styles.activeLike]}
      >
        <Text style={styles.label}>{reaction === "LIKE" ? "Liked" : "Like"}</Text>
      </Pressable>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ selected: reaction === "DISLIKE", disabled }}
        disabled={disabled}
        onPress={() => onChange(reaction === "DISLIKE" ? "NONE" : "DISLIKE")}
        style={[styles.button, reaction === "DISLIKE" && styles.activeDislike]}
      >
        <Text style={styles.label}>{reaction === "DISLIKE" ? "Disliked" : "Dislike"}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 8 },
  button: {
    borderWidth: 1,
    borderColor: "#D0D5DD",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  activeLike: { backgroundColor: "#E8F5E9", borderColor: "#2E7D32" },
  activeDislike: { backgroundColor: "#FFEBEE", borderColor: "#C62828" },
  label: { fontSize: 13, color: "#111827", fontWeight: "500" },
});
