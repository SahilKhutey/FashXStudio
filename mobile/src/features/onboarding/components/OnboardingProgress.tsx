import React from "react";
import { View, Text, StyleSheet } from "react-native";

type Props = {
  current: number;
  total: number;
};

export function OnboardingProgress({ current, total }: Props) {
  const safeTotal = Math.max(1, total);
  const progress = Math.min(1, Math.max(0, current / safeTotal));

  return (
    <View style={styles.container}>
      <Text style={styles.label}>
        Step {current} of {safeTotal}
      </Text>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${progress * 100}%` }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 8 },
  label: { fontSize: 12, color: "#6B7280" },
  track: {
    height: 5,
    backgroundColor: "#E5E7EB",
    borderRadius: 5,
    overflow: "hidden",
  },
  fill: {
    height: 5,
    backgroundColor: "#111827",
    borderRadius: 5,
  },
});
