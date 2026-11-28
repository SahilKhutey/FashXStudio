import React from "react";
import { View, Text, Pressable, StyleSheet } from "react-native";
import { SkipStepButton } from "../components/SkipStepButton";

type Props = {
  onContinue: () => void;
  onSkip: () => void;
};

export function ProductIntroScreen({ onContinue, onSkip }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        How FashXStudio works
      </Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>1. Fashion discovery</Text>
        <Text style={styles.cardBody}>
          Browse products from participating merchants and find styles that match your preferences.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>2. Virtual Try-On</Text>
        <Text style={styles.cardBody}>
          Virtual Try-On is an AI-generated visual representation. It does not verify garment size, physical fit, comfort or real-life appearance.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>3. Fit guidance</Text>
        <Text style={styles.cardBody}>
          Receive size guidance when sufficient shopper measurements and verified merchant size-chart information are available. Fit guidance does not guarantee physical fit or comfort.
        </Text>
      </View>

      <Pressable style={styles.button} onPress={onContinue} accessibilityRole="button">
        <Text style={styles.buttonText}>Continue</Text>
      </Pressable>
      <SkipStepButton onSkip={onSkip} label="Skip introduction" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, gap: 14 },
  title: { fontSize: 24, fontWeight: "700", color: "#111827" },
  card: {
    backgroundColor: "#F9FAFB",
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    gap: 4,
  },
  cardTitle: { fontSize: 15, fontWeight: "700", color: "#111827" },
  cardBody: { fontSize: 13, lineHeight: 19, color: "#4B5563" },
  button: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 4,
  },
  buttonText: { color: "#fff", fontWeight: "600" },
});
