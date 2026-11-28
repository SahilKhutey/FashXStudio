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
  onVerificationRequired: (email: string) => void;
  onAuthenticated?: () => void;
  onLoginPress: () => void;
};

export function RegisterScreen({
  onVerificationRequired,
  onAuthenticated,
  onLoginPress,
}: Props) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRegister() {
    if (loading) return;
    setError(null);

    const trimmedName = name.trim();
    const normalizedEmail = email.trim().toLowerCase();

    if (trimmedName.length < 2) {
      setError("Please enter your full name.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setError("Please enter a valid email address.");
      return;
    }

    if (password.length < 12) {
      setError("Password must be at least 12 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (!acceptedTerms) {
      setError("Please accept the Terms and Privacy Policy.");
      return;
    }

    setLoading(true);
    try {
      const result = await authProviderService.register({
        name: trimmedName,
        email: normalizedEmail,
        password,
      });

      if (result.status === "VERIFICATION_REQUIRED") {
        onVerificationRequired(normalizedEmail);
      } else if (result.status === "AUTHENTICATED") {
        onAuthenticated?.();
      }
    } catch (err) {
      setError(authProviderService.getUserMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Create your account
      </Text>

      <TextInput
        style={styles.input}
        value={name}
        onChangeText={setName}
        placeholder="Full name"
        autoCapitalize="words"
        editable={!loading}
        accessibilityLabel="Full name"
      />

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

      <TextInput
        style={styles.input}
        value={password}
        onChangeText={setPassword}
        placeholder="Password (min 12 characters)"
        secureTextEntry
        editable={!loading}
        accessibilityLabel="Password"
      />

      <TextInput
        style={styles.input}
        value={confirmPassword}
        onChangeText={setConfirmPassword}
        placeholder="Confirm password"
        secureTextEntry
        editable={!loading}
        accessibilityLabel="Confirm password"
      />

      <Pressable
        onPress={() => setAcceptedTerms((value) => !value)}
        accessibilityRole="checkbox"
        accessibilityState={{ checked: acceptedTerms }}
        style={styles.termsRow}
      >
        <Text style={styles.termsText}>
          {acceptedTerms ? "[x]" : "[ ]"} I accept the Terms and Privacy Policy
        </Text>
      </Pressable>

      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : null}

      <Pressable
        disabled={loading}
        onPress={() => {
          void handleRegister();
        }}
        style={styles.button}
        accessibilityRole="button"
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Create account</Text>
        )}
      </Pressable>

      <Pressable onPress={onLoginPress} disabled={loading} style={styles.link}>
        <Text style={styles.linkText}>Already have an account? Sign in</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, justifyContent: "center", gap: 14 },
  title: { fontSize: 26, fontWeight: "700", color: "#111827" },
  input: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    backgroundColor: "#fff",
  },
  termsRow: { paddingVertical: 4 },
  termsText: { color: "#374151", fontSize: 14 },
  button: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontWeight: "600" },
  error: { color: "#B42318", fontSize: 14 },
  link: { alignItems: "center", paddingTop: 8 },
  linkText: { color: "#4F46E5", fontWeight: "500" },
});
