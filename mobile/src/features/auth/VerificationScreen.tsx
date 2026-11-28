import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  ActivityIndicator,
  StyleSheet,
} from "react-native";
import { authProviderService } from "../../auth/auth.instance";
import { maskEmail } from "../../auth/auth.types";

type Props = {
  email: string;
  onVerified: () => void;
  onBackToLogin: () => void;
};

export function VerificationScreen({
  email,
  onVerified,
  onBackToLogin,
}: Props) {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function handleVerify() {
    if (loading) return;
    setError(null);
    setMessage(null);

    const normalizedCode = code.trim();
    if (!/^\d{6}$/.test(normalizedCode)) {
      setError("Enter the six-digit verification code.");
      return;
    }

    setLoading(true);
    try {
      await authProviderService.confirmRegistration({
        email,
        code: normalizedCode,
      });
      onVerified();
    } catch (err) {
      setError(authProviderService.getUserMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    if (resending || loading) return;
    setError(null);
    setMessage(null);
    setResending(true);

    try {
      await authProviderService.resendVerificationCode(email);
      setMessage("A new verification code has been requested.");
    } catch (err) {
      setError(authProviderService.getUserMessage(err));
    } finally {
      setResending(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Verify your email
      </Text>

      <Text style={styles.subtitle}>
        Enter the verification code sent to {maskEmail(email)}.
      </Text>

      <TextInput
        style={styles.input}
        value={code}
        onChangeText={(value) => setCode(value.replace(/\D/g, "").slice(0, 6))}
        keyboardType="number-pad"
        maxLength={6}
        placeholder="Verification code"
        editable={!loading}
        accessibilityLabel="Verification code"
      />

      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : null}

      {message ? <Text style={styles.info}>{message}</Text> : null}

      <Pressable
        disabled={loading}
        onPress={() => {
          void handleVerify();
        }}
        style={styles.button}
        accessibilityRole="button"
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Verify account</Text>
        )}
      </Pressable>

      <Pressable
        disabled={resending || loading}
        onPress={() => {
          void handleResend();
        }}
        style={styles.link}
      >
        <Text style={styles.linkText}>
          {resending ? "Requesting..." : "Resend verification code"}
        </Text>
      </Pressable>

      <Pressable onPress={onBackToLogin} style={styles.link}>
        <Text style={styles.linkText}>Back to login</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, gap: 14 },
  title: { fontSize: 26, fontWeight: "700", color: "#111827" },
  subtitle: { fontSize: 14, color: "#4B5563" },
  input: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    backgroundColor: "#fff",
  },
  button: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontWeight: "600" },
  error: { color: "#B42318", fontSize: 14 },
  info: { color: "#065F46", fontSize: 14 },
  link: { alignItems: "center", paddingTop: 6 },
  linkText: { color: "#4F46E5", fontWeight: "500" },
});
