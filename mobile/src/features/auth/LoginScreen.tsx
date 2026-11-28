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
  onAuthenticated: () => void;
  onRegisterPress: () => void;
  onForgotPassword: () => void;
  onVerificationRequired: (email: string) => void;
};

export function LoginScreen({
  onAuthenticated,
  onRegisterPress,
  onForgotPassword,
  onVerificationRequired,
}: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLogin() {
    if (loading) return;
    setError(null);

    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password) {
      setError("Enter your email address and password.");
      return;
    }

    setLoading(true);
    try {
      const result = await authProviderService.login({
        email: normalizedEmail,
        password,
      });

      if (result.status === "AUTHENTICATED") {
        onAuthenticated();
      } else if (result.status === "VERIFICATION_REQUIRED") {
        onVerificationRequired(result.email);
      }
    } catch (err) {
      setPassword("");
      setError(authProviderService.getUserMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Welcome back
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

      <TextInput
        style={styles.input}
        value={password}
        onChangeText={setPassword}
        placeholder="Password"
        secureTextEntry
        editable={!loading}
        accessibilityLabel="Password"
      />

      <Pressable onPress={onForgotPassword} disabled={loading}>
        <Text style={styles.linkText}>Forgot password?</Text>
      </Pressable>

      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : null}

      <Pressable
        disabled={loading}
        onPress={() => {
          void handleLogin();
        }}
        style={styles.button}
        accessibilityRole="button"
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Sign in</Text>
        )}
      </Pressable>

      <Pressable onPress={onRegisterPress} disabled={loading} style={styles.link}>
        <Text style={styles.linkText}>New to FashXStudio? Create an account</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, gap: 14 },
  title: { fontSize: 26, fontWeight: "700", color: "#111827" },
  input: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    backgroundColor: "#fff",
  },
  button: {
    padding: 16,
    backgroundColor: "#111827",
    borderRadius: 12,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontWeight: "600" },
  error: { color: "#B42318", fontSize: 14 },
  link: { alignItems: "center", paddingTop: 8 },
  linkText: { color: "#4F46E5", fontWeight: "500" },
});
