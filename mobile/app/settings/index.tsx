import React from "react";
import { StyleSheet, Text, View, TouchableOpacity, ScrollView } from "react-native";
import { useRouter } from "expo-router";
import { useAuthStore } from "../../src/features/auth/authStore";

export default function SettingsScreen() {
  const router = useRouter();
  const { signOut, me } = useAuthStore();

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Settings</Text>
      <Text style={styles.subtitle}>Account & Privacy (Slice 4 Stub)</Text>

      <View style={styles.card}>
        <Text style={styles.cardHeader}>User Identity</Text>
        <Text style={styles.infoText}>User ID: {me?.user_id || "Unknown"}</Text>
        <Text style={styles.infoText}>Roles: {me?.roles?.join(", ") || "user"}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardHeader}>Privacy Controls</Text>
        <Text style={styles.placeholderText}>
          Consent management, photo deletion, and account erasure will be available in Slice 4.
        </Text>
      </View>

      <TouchableOpacity
        style={styles.signOutButton}
        onPress={() => signOut()}
        accessibilityRole="button"
        accessibilityLabel="Sign out"
      >
        <Text style={styles.signOutText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    backgroundColor: "#F9FAFB",
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#6B7280",
    marginBottom: 20,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  cardHeader: {
    fontSize: 15,
    fontWeight: "600",
    color: "#1F2937",
    marginBottom: 8,
  },
  infoText: {
    fontSize: 13,
    color: "#4B5563",
    marginBottom: 4,
  },
  placeholderText: {
    fontSize: 13,
    color: "#9CA3AF",
    lineHeight: 18,
  },
  signOutButton: {
    backgroundColor: "#EF4444",
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 20,
  },
  signOutText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
  },
});
