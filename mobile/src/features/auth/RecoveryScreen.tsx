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

type Props = {
  onRecoveryComplete: () => void;
  onBackToLogin: () => void;
};

export function RecoveryScreen({
  onRecoveryComplete,
  onBackToLogin,
}: Props) {
  const [step, setStep] = useState<"request" | "reset">("request");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function handleRequestRecovery() {
    if (loading) return;
    setError(null);
    setMessage(null);

    const normalizedEmail = email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setError("Please enter a valid email address.");
      return;
    }

    setLoading(true);
    try {
      await authProviderService.startRecovery({ email: normalizedEmail });
      setMessage("If an account exists for this email, recovery instructions have been sent.");
      setStep("reset");
    } catch (err) {
      setError(authProviderService.getUserMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleCompleteRecovery() {
    if (loading) return;
    setError(null);
    setMessage(null);

    const normalizedEmail = email.trim().toLowerCase();
    const normalizedCode = code.trim();
    if (!/^\d{6}$/.test(normalizedCode)) {
      setError("Enter the six-digit recovery code.");
      return;
    }
    if (newPassword.length < 12) {
      setError("Password must be at least 12 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await authProviderService.completeRecovery({
        email: normalizedEmail,
        code: normalizedCode,
        newPassword,
      });
      onRecoveryComplete();
    } catch (err) {
      setError(authProviderService.getUserMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        {step === "request" ? "Reset your password" : "Choose a new password"}
      </Text>

      {step === "request" ? (
        <>
          <Text style={styles.subtitle}>
            Enter your account email to begin password recovery.
          </Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            placeholder="Email address"
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            editable={!loading}
            accessibilityLabel="Email address"
          />
          {error ? (
            <Text accessibilityRole="alert" style={styles.error}>
              {error}
            </Text>
          ) : null}
          <Pressable
            disabled={loading}
            onPress={() => {
              void handleRequestRecovery();
            }}
            style={styles.button}
            accessibilityRole="button"
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Send recovery code</Text>
            )}
          </Pressable>
        </>
      ) : (
        <>
          {message ? <Text style={styles.info}>{message}</Text> : null}
          <TextInput
            style={styles.input}
            value={code}
            onChangeText={(value) => setCode(value.replace(/\D/g, "").slice(0, 6))}
            keyboardType="number-pad"
            maxLength={6}
            placeholder="Recovery code"
            editable={!loading}
            accessibilityLabel="Recovery code"
          />
          <TextInput
            style={styles.input}
            value={newPassword}
            onChangeText={setNewPassword}
            placeholder="New password (min 12 characters)"
            secureTextEntry
            editable={!loading}
            accessibilityLabel="New password"
          />
          <TextInput
            style={styles.input}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            placeholder="Confirm new password"
            secureTextEntry
            editable={!loading}
            accessibilityLabel="Confirm new password"
          />
          {error ? (
            <Text accessibilityRole="alert" style={styles.error}>
              {error}
            </Text>
          ) : null}
          <Pressable
            disabled={loading}
            onPress={() => {
              void handleCompleteRecovery();
            }}
            style={styles.button}
            accessibilityRole="button"
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Reset password</Text>
            )}
          </Pressable>
        </>
      )}

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
  link: { alignItems: "center", paddingTop: 8 },
  linkText: { color: "#4F46E5", fontWeight: "500" },
});
