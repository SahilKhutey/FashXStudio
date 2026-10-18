import React, { useEffect } from "react";
import { StyleSheet, Text, View, TouchableOpacity, ScrollView } from "react-native";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../src/features/auth/authStore";
import { useMe } from "../src/api/hooks";

export default function HomeScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { session, signOut } = useAuthStore();
  const { data: me } = useMe(true);

  useEffect(() => {
    if (me?.onboarding && !me.onboarding.complete) {
      const missing = me.onboarding.missing || [];
      if (missing.includes("consent")) {
        router.replace("/onboarding/consent");
      } else if (missing.includes("profile")) {
        router.replace("/onboarding/profile");
      } else if (missing.includes("style_quiz")) {
        router.replace("/onboarding/quiz");
      } else if (missing.includes("photo")) {
        router.replace("/onboarding/capture");
      }
    }
  }, [me?.onboarding, router]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        FashX Studio
      </Text>
      <Text style={styles.subtitle}>Mobile Foundation 8A Ready</Text>

      <View style={styles.infoCard}>
        <Text style={styles.sectionHeader}>Session Details</Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Email: </Text>
          {session?.user?.email || "Unknown"}
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Supabase Subject: </Text>
          {session?.user?.id || "None"}
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Backend User ID: </Text>
          {me?.user_id || "Resolving /me..."}
        </Text>
        <Text style={styles.infoText}>
          <Text style={styles.bold}>Roles: </Text>
          {me?.roles?.join(", ") || "user"}
        </Text>
      </View>

      <TouchableOpacity
        style={styles.signOutButton}
        onPress={() => signOut()}
        accessibilityRole="button"
        accessibilityLabel={t("auth.signOut")}
      >
        <Text style={styles.signOutText}>{t("auth.signOut")}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    backgroundColor: "#F9FAFB",
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: "#111827",
  },
  subtitle: {
    marginTop: 6,
    fontSize: 16,
    color: "#4B5563",
    marginBottom: 24,
  },
  infoCard: {
    width: "100%",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
    marginBottom: 24,
  },
  sectionHeader: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1F2937",
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: "#374151",
    marginBottom: 8,
  },
  bold: {
    fontWeight: "600",
  },
  signOutButton: {
    width: "100%",
    height: 48,
    backgroundColor: "#EF4444",
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
  },
  signOutText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
});
