import React from "react";
import { StyleSheet, Text, View } from "react-native";

export interface VisualTryOnDisclosureProps {
  /** Optional custom styling container */
  style?: object;
  /** Whether to show compact mode (e.g. for preview cards) */
  compact?: boolean;
}

/**
 * VisualTryOnDisclosure Component (Phase 07.8 - Task 7.8.1)
 *
 * Enforces mandatory shopper-facing distinction that AI-generated Virtual Try-On
 * visual results do NOT verify physical garment fit, size accuracy, or dimensions.
 */
export function VisualTryOnDisclosure({ style, compact = false }: VisualTryOnDisclosureProps) {
  return (
    <View
      accessible={true}
      accessibilityRole="summary"
      accessibilityLabel="AI-generated visual try-on disclosure. This image shows how the garment might look on you. It does not verify the garment's physical size or fit."
      style={[styles.container, compact && styles.containerCompact, style]}
    >
      <View style={styles.headerRow}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>AI SIMULATION</Text>
        </View>
        <Text style={styles.title}>AI-generated visual try-on</Text>
      </View>

      <Text style={styles.description}>
        This image shows how the garment might look on you. It does not verify the garment's physical size or fit.
      </Text>

      {!compact && (
        <Text style={styles.secondary}>
          Check the merchant's size chart and available fit guidance separately before choosing a size.
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 14,
    borderRadius: 12,
    backgroundColor: "#F2F4F7",
    borderWidth: 1,
    borderColor: "#E4E7EC",
    gap: 8,
  },
  containerCompact: {
    padding: 10,
    gap: 4,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  badge: {
    backgroundColor: "#344054",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  badgeText: {
    color: "#FFFFFF",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  title: {
    fontSize: 14,
    fontWeight: "700",
    color: "#1D2939",
  },
  description: {
    fontSize: 13,
    lineHeight: 18,
    color: "#344054",
  },
  secondary: {
    fontSize: 12,
    lineHeight: 16,
    color: "#475467",
  },
});
