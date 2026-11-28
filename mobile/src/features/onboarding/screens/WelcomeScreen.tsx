import React from "react";
import { View, Text, Pressable, StyleSheet } from "react-native";

type Props = {
  onContinue: () => void;
};

export function WelcomeScreen({ onContinue }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.brand}>FashXStudio</Text>
      <Text style={styles.title} accessibilityRole="header">
        Fashion that understands you.
      </Text>
      <Text style={styles.description}>
        Discover clothing, explore styles and see AI-generated virtual try-on previews using your own permitted photos.
      </Text>
      <Text style={styles.privacy}>
        Your profile helps us personalize the experience. You control the optional information you share.
      </Text>
      <Pressable
        style={styles.button}
        onPress={onContinue}
        accessibilityRole="button"
      >
        <Text style={styles.buttonText}>Get started</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, gap: 18 },
  brand: { fontSize: 18, fontWeight: "700", color: "#4F46E5" },
  title: { fontSize: 30, fontWeight: "800", color: "#111827" },
  description: { fontSize: 16, lineHeight: 24, color: "#374151" },
  privacy: { fontSize: 13, color: "#6B7280" },
  button: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontWeight: "600" },
});
