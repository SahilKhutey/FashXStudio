import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FitPreference } from "../types";

const OPTIONS: { value: FitPreference; label: string; description: string }[] = [
  { value: "SLIM", label: "Slim", description: "Closer to the body, less extra room" },
  { value: "REGULAR", label: "Regular", description: "Balanced fit, neither close nor loose" },
  { value: "RELAXED", label: "Relaxed", description: "More room and a looser feel" },
  { value: "OVERSIZED", label: "Oversized", description: "Intentionally roomy silhouette" },
  { value: "NO_PREFERENCE", label: "No preference", description: "Keep neutral" },
];

interface Props {
  title: string;
  selected: FitPreference;
  onSelect: (preference: FitPreference) => void;
}

export function FitPreferenceSelector({ title, selected, onSelect }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.optionsRow} accessibilityRole="radiogroup">
        {OPTIONS.map((opt) => {
          const isSelected = selected === opt.value;
          return (
            <Pressable
              key={opt.value}
              style={[styles.pill, isSelected && styles.selectedPill]}
              onPress={() => onSelect(opt.value)}
              accessibilityRole="radio"
              accessibilityState={{ selected: isSelected }}
              accessibilityLabel={`${title}: ${opt.label}`}
            >
              <Text
                style={[styles.pillText, isSelected && styles.selectedPillText]}
              >
                {opt.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
      <Text style={styles.note}>
        Fit preference expresses personal comfort and is not physical-fit verification or a universal brand size.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    marginVertical: 8,
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
  },
  optionsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  pill: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    backgroundColor: "#F9FAFB",
  },
  selectedPill: {
    borderColor: "#0F766E",
    backgroundColor: "#F0FDFA",
  },
  pillText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#374151",
  },
  selectedPillText: {
    color: "#0F766E",
  },
  note: {
    marginTop: 8,
    fontSize: 11,
    color: "#6B7280",
    fontStyle: "italic",
  },
});
