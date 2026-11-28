import React from "react";
import { View, Image, Text, Pressable, StyleSheet } from "react-native";
import { VisualSimulationNotice } from "./VisualSimulationNotice";

interface Props {
  uri: string;
  submitting?: boolean;
  onRetake: () => void;
  onConfirm: () => void;
}

export function PhotoPreview({
  uri,
  submitting = false,
  onRetake,
  onConfirm,
}: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Review your photo
      </Text>

      <Image
        source={{ uri }}
        resizeMode="contain"
        style={styles.image}
        accessibilityLabel="Selected shopper photo preview"
      />

      <Text style={styles.consentText}>
        Your photo will be processed to generate a virtual try-on image for this product and may be sent to our approved AI processing provider.
      </Text>

      <VisualSimulationNotice />

      <Pressable
        disabled={submitting}
        onPress={onRetake}
        accessibilityRole="button"
        style={styles.secondaryButton}
      >
        <Text style={styles.secondaryText}>Retake or choose another photo</Text>
      </Pressable>

      <Pressable
        disabled={submitting}
        onPress={onConfirm}
        accessibilityRole="button"
        style={styles.primaryButton}
      >
        <Text style={styles.primaryText}>
          {submitting ? "Submitting..." : "Confirm & start try-on"}
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, gap: 12 },
  title: { fontSize: 22, fontWeight: "700", color: "#111827" },
  image: { width: "100%", flex: 1, borderRadius: 12, backgroundColor: "#F3F4F6" },
  consentText: { fontSize: 13, lineHeight: 19, color: "#4B5563" },
  secondaryButton: {
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    alignItems: "center",
  },
  secondaryText: { fontWeight: "600", color: "#111827" },
  primaryButton: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: "#111827",
    alignItems: "center",
  },
  primaryText: { fontWeight: "600", color: "#FFFFFF" },
});
