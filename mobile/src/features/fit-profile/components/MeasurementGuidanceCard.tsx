import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { MeasurementDefinition } from "../types";

interface Props {
  definition: MeasurementDefinition;
}

export function MeasurementGuidanceCard({ definition }: Props) {
  return (
    <View style={styles.card} accessible={true} accessibilityRole="summary">
      <Text style={styles.title}>How to measure: {definition.display_name}</Text>
      <Text style={styles.explanation}>{definition.explanation}</Text>
      <Text style={styles.detail}>Tape position: {definition.tape_positioning}</Text>
      <Text style={styles.detail}>Keep tape relaxed: {definition.how_to_hold}</Text>
      <Text style={styles.example}>Example: {definition.example_input}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#F8FAFC",
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    marginBottom: 10,
  },
  title: {
    fontSize: 14,
    fontWeight: "700",
    color: "#0F172A",
    marginBottom: 4,
  },
  explanation: {
    fontSize: 13,
    color: "#334155",
    lineHeight: 18,
    marginBottom: 6,
  },
  detail: {
    fontSize: 12,
    color: "#475569",
    marginBottom: 2,
  },
  example: {
    marginTop: 4,
    fontSize: 12,
    fontWeight: "600",
    color: "#0F766E",
  },
});
