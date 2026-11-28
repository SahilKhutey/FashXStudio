import React from "react";
import { Pressable, Text, StyleSheet } from "react-native";

type Props = {
  onSkip: () => void;
  label?: string;
};

export function SkipStepButton({ onSkip, label = "Skip for now" }: Props) {
  return (
    <Pressable
      onPress={onSkip}
      accessibilityRole="button"
      style={styles.container}
    >
      <Text style={styles.label}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: "center", paddingVertical: 12 },
  label: { fontSize: 14, color: "#6B7280", fontWeight: "500" },
});
