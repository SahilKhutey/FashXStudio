import React, { useState, useEffect } from "react";
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
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { supabase } from "../../src/lib/supabase";

export default function VerifyScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const params = useLocalSearchParams<{ email: string }>();
  const email = params.email || "";

  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [cooldown, setCooldown] = useState(30);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleVerifyOtp = async () => {
    const trimmedCode = code.trim();
    if (trimmedCode.length < 6) {
      setErrorMessage("Please enter the 6-digit code.");
      return;
    }

    setLoading(true);
    setErrorMessage(null);

    try {
      const { data, error } = await supabase.auth.verifyOtp({
        email,
        token: trimmedCode,
        type: "email",
      });

      if (error || !data.session) {
        setErrorMessage(t("auth.invalidCode"));
        return;
      }

      // Successful verification; _layout listener will handle redirection
    } catch {
      setErrorMessage(t("common.networkError"));
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || resending) return;
    setResending(true);
    setErrorMessage(null);

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { shouldCreateUser: false },
      });
      if (error) {
        setErrorMessage(error.message);
      } else {
        setCooldown(30);
      }
    } catch {
      setErrorMessage(t("common.networkError"));
    } finally {
      setResending(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <View style={styles.card}>
        <Text style={styles.title} accessibilityRole="header">
          {t("auth.verifyTitle")}
        </Text>
        <Text style={styles.subtitle}>
          {t("auth.verifySubtitle", { email })}
        </Text>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>{t("auth.codeLabel")}</Text>
          <TextInput
            style={styles.input}
            placeholder={t("auth.codePlaceholder")}
            placeholderTextColor="#888"
            keyboardType="number-pad"
            maxLength={8}
            autoFocus
            value={code}
            onChangeText={(txt) => {
              setCode(txt);
              if (errorMessage) setErrorMessage(null);
            }}
            accessibilityLabel={t("auth.codeLabel")}
          />
        </View>

        {errorMessage ? (
          <View style={styles.errorBox} accessibilityRole="alert">
            <Text style={styles.errorText}>{errorMessage}</Text>
          </View>
        ) : null}

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleVerifyOtp}
          disabled={loading}
          accessibilityRole="button"
          accessibilityLabel={t("auth.verifyButton")}
        >
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.buttonText}>{t("auth.verifyButton")}</Text>
          )}
        </TouchableOpacity>

        <View style={styles.footer}>
          <TouchableOpacity
            onPress={handleResend}
            disabled={cooldown > 0 || resending}
            accessibilityRole="button"
            accessibilityLabel={
              cooldown > 0
                ? t("auth.resendCooldown", { seconds: cooldown })
                : t("auth.resendCode")
            }
          >
            <Text
              style={[
                styles.resendText,
                (cooldown > 0 || resending) && styles.resendDisabled,
              ]}
            >
              {cooldown > 0
                ? t("auth.resendCooldown", { seconds: cooldown })
                : t("auth.resendCode")}
            </Text>
          </TouchableOpacity>
        </View>
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
    lineHeight: 20,
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
    height: 48,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 8,
    paddingHorizontal: 14,
    fontSize: 20,
    letterSpacing: 4,
    textAlign: "center",
    color: "#111827",
    backgroundColor: "#FDFDFD",
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
  footer: {
    marginTop: 20,
    alignItems: "center",
  },
  resendText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#4F46E5",
  },
  resendDisabled: {
    color: "#9CA3AF",
  },
});
