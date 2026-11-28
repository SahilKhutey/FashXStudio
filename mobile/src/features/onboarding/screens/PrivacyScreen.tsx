import React from "react";
import { View, Text, Pressable, StyleSheet } from "react-native";

type Props = {
  privacyUrl?: string | null;
  onOpenPolicy?: (url: string) => void;
  onContinue: () => void;
};

export function PrivacyScreen({ privacyUrl, onOpenPolicy, onContinue }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Your information, your choice.
      </Text>
      <Text style={styles.body}>
        We use information you choose to provide to improve your shopping experience.
      </Text>
      <Text style={styles.item}>
        Profile information: Display name, height, size system and preferences personalize discovery and presentation.
      </Text>
      <Text style={styles.item}>
        Body measurements: Optional measurements are compared with verified merchant size charts when supported.
      </Text>
      <Text style={styles.item}>
        Photos and Virtual Try-On: A photo is not needed to create a basic profile. Third-party VTO processing requires separate explicit consent.
      </Text>

      {privacyUrl && onOpenPolicy ? (
        <Pressable
          accessibilityRole="link"
          onPress={() => onOpenPolicy(privacyUrl)}
          style={styles.link}
        >
          <Text style={styles.linkText}>Read full Privacy Policy</Text>
        </Pressable>
      ) : null}

      <Pressable style={styles.button} onPress={onContinue} accessibilityRole="button">
        <Text style={styles.buttonText}>Review consent choices</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, gap: 14 },
  title: { fontSize: 24, fontWeight: "700", color: "#111827" },
  body: { fontSize: 15, color: "#374151" },
  item: { fontSize: 13, lineHeight: 19, color: "#4B5563" },
  link: { paddingVertical: 6 },
  linkText: { color: "#4F46E5", fontWeight: "600" },
  button: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontWeight: "600" },
});
