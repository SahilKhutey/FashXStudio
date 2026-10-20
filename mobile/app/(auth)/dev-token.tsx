import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { setDevToken } from "../../src/lib/token";
import { useAuthStore, UserMe } from "../../src/features/auth/authStore";
import { api } from "../../src/api/client";

export const isDevTokenEnabled = (
  isDev: boolean = typeof __DEV__ !== "undefined"
    ? Boolean(__DEV__)
    : process.env.NODE_ENV !== "production",
  flag: string | undefined = process.env.EXPO_PUBLIC_DEV_TOKEN_LOGIN
): boolean => {
  return isDev && flag === "1";
};

export default function DevTokenScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { setDevSession, setMe } = useAuthStore();
  const [tokenInput, setTokenInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const enabled = isDevTokenEnabled();

  useEffect(() => {
    if (!enabled) {
      router.replace("/(auth)/sign-in");
    }
  }, [enabled, router]);

  if (!enabled) {
    return null;
  }

  const handleUseToken = async () => {
    const trimmed = tokenInput.trim();
    if (!trimmed) {
      setErrorMessage("Please enter or paste a JWT dev token.");
      return;
    }

    setLoading(true);
    setErrorMessage(null);

    try {
      setDevToken(trimmed);
      setDevSession(true);
      const me = await api<UserMe>("/me");
      setMe(me);
      router.replace("/");
    } catch (err: any) {
      setDevToken(null);
      setDevSession(false);
      setErrorMessage(err.message || "Failed to validate dev token with /me");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <View style={styles.card} testID="dev-token-card">
        <Text style={styles.badge}>DEVELOPMENT ONLY</Text>
        <Text style={styles.title} accessibilityRole="header">
          {t("dev.tokenTitle")}
        </Text>
        <Text style={styles.subtitle}>
          {t("dev.tokenSubtitle")}
        </Text>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>{t("dev.tokenLabel")}</Text>
          <TextInput
            style={styles.input}
            placeholder={t("dev.tokenPlaceholder")}
            placeholderTextColor="#888"
            multiline
            numberOfLines={4}
            autoCapitalize="none"
            autoCorrect={false}
            value={tokenInput}
            onChangeText={(txt) => {
              setTokenInput(txt);
              if (errorMessage) setErrorMessage(null);
            }}
            accessibilityLabel={t("dev.tokenLabel")}
            testID="dev-token-input"
          />
        </View>

        {errorMessage ? (
          <View style={styles.errorBox} accessibilityRole="alert">
            <Text style={styles.errorText}>{errorMessage}</Text>
          </View>
        ) : null}

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleUseToken}
          disabled={loading}
          accessibilityRole="button"
          accessibilityLabel={t("dev.useToken")}
          testID="dev-token-submit"
        >
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.buttonText}>{t("dev.useToken")}</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.replace("/(auth)/sign-in")}
          accessibilityRole="button"
          accessibilityLabel={t("dev.backToSignIn")}
        >
          <Text style={styles.backButtonText}>{t("dev.backToSignIn")}</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
    justifyContent: "center",
    padding: 24,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 28,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  badge: {
    alignSelf: "center",
    backgroundColor: "#FEF3C7",
    color: "#92400E",
    fontSize: 11,
    fontWeight: "700",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginBottom: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
    textAlign: "center",
  },
  subtitle: {
    fontSize: 14,
    color: "#6B7280",
    marginBottom: 24,
    textAlign: "center",
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: "#374151",
    marginBottom: 6,
  },
  input: {
    minHeight: 80,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 14,
    color: "#111827",
    backgroundColor: "#FDFDFD",
    textAlignVertical: "top",
  },
  errorBox: {
    backgroundColor: "#FEF2F2",
    borderColor: "#FCA5A5",
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    color: "#B91C1C",
    fontSize: 13,
    lineHeight: 18,
  },
  button: {
    height: 48,
    backgroundColor: "#4F46E5",
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
  backButton: {
    marginTop: 16,
    paddingVertical: 8,
    alignItems: "center",
  },
  backButtonText: {
    color: "#4B5563",
    fontSize: 14,
    fontWeight: "500",
  },
});
