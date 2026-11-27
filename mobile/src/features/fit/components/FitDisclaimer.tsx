import React from "react";
import { StyleSheet, Text, View } from "react-native";

export interface FitDisclaimerProps {
  text?: string;
}

const DEFAULT_DISCLAIMER =
  "This is size guidance based on available product and shopper information. It does not guarantee physical fit, comfort or appearance.";

export function FitDisclaimer({ text }: FitDisclaimerProps) {
  return (
    <View style={styles.container} testID="fit-disclaimer">
      <Text style={styles.text}>{text || DEFAULT_DISCLAIMER}</Text>
      <Text style={styles.vtoNote}>
        Visual try-on shows appearance simulation only and is separate from physical size guidance.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },
  text: {
    fontSize: 12,
    lineHeight: 16,
    color: "#4B5563",
  },
  vtoNote: {
    marginTop: 4,
    fontSize: 11,
    lineHeight: 15,
    color: "#6B7280",
  },
});
