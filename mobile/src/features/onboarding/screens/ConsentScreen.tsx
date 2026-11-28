import React, { useState } from "react";
import { View, Text, Switch, Pressable, StyleSheet } from "react-native";
import { savePurposeConsent } from "../consent.api";

type Props = {
  noticeVersion: string;
  onComplete: () => void;
};

/**
 * Purpose-specific optional consent controls.
 * All optional purposes start disabled (false) and never bundle model training.
 */
export function ConsentScreen({ noticeVersion, onComplete }: Props) {
  const [personalizedRanking, setPersonalizedRanking] = useState(false);
  const [thirdPartyVto, setThirdPartyVto] = useState(false);
  const [analytics, setAnalytics] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (saving) return;
    setSaving(true);
    setError(null);

    try {
      await Promise.all([
        savePurposeConsent({
          purpose: "PERSONALIZED_RANKING",
          granted: personalizedRanking,
          noticeVersion,
        }),
        savePurposeConsent({
          purpose: "THIRD_PARTY_VTO_PROCESSING",
          granted: thirdPartyVto,
          noticeVersion,
        }),
        savePurposeConsent({
          purpose: "PRODUCT_ANALYTICS",
          granted: analytics,
          noticeVersion,
        }),
      ]);
      onComplete();
    } catch {
      setError("Could not save your consent preferences. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Choose how we use your information
      </Text>
      <Text style={styles.subtitle}>
        You can change optional choices later in Privacy Settings. Declining optional processing does not block basic browsing.
      </Text>

      <View style={styles.row}>
        <View style={styles.rowText}>
          <Text style={styles.rowTitle}>Allow personalization</Text>
          <Text style={styles.rowSub}>Optional personalized product ranking</Text>
        </View>
        <Switch
          value={personalizedRanking}
          onValueChange={setPersonalizedRanking}
          accessibilityLabel="Allow personalization"
        />
      </View>

      <View style={styles.row}>
        <View style={styles.rowText}>
          <Text style={styles.rowTitle}>Allow third-party VTO processing</Text>
          <Text style={styles.rowSub}>Separate explicit consent for Virtual Try-On</Text>
        </View>
        <Switch
          value={thirdPartyVto}
          onValueChange={setThirdPartyVto}
          accessibilityLabel="Allow third-party VTO processing"
        />
      </View>

      <View style={styles.row}>
        <View style={styles.rowText}>
          <Text style={styles.rowTitle}>Allow analytics</Text>
          <Text style={styles.rowSub}>Optional product usage analytics</Text>
        </View>
        <Switch
          value={analytics}
          onValueChange={setAnalytics}
          accessibilityLabel="Allow analytics"
        />
      </View>

      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : null}

      <Pressable
        disabled={saving}
        onPress={() => {
          void handleSave();
        }}
        style={styles.button}
        accessibilityRole="button"
      >
        <Text style={styles.buttonText}>
          {saving ? "Saving..." : "Save choices"}
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, gap: 16 },
  title: { fontSize: 22, fontWeight: "700", color: "#111827" },
  subtitle: { fontSize: 13, color: "#4B5563" },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    paddingVertical: 6,
  },
  rowText: { flex: 1 },
  rowTitle: { fontSize: 15, fontWeight: "600", color: "#111827" },
  rowSub: { fontSize: 12, color: "#6B7280" },
  error: { color: "#B42318", fontSize: 13 },
  button: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontWeight: "600" },
});
