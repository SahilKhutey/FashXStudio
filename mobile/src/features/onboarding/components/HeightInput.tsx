import React, { useState } from "react";
import { View, Text, TextInput, Pressable, StyleSheet } from "react-native";
import { SkipStepButton } from "../components/SkipStepButton";

type Props = {
  onSubmit: (valueCm: number) => void;
  onSkip: () => void;
};

export function HeightInput({ onSubmit, onSkip }: Props) {
  const [value, setValue] = useState("");
  const [unit, setUnit] = useState<"CM" | "IN">("CM");
  const [error, setError] = useState<string | null>(null);

  function submit() {
    const parsed = Number(value);
    if (!value.trim() || !Number.isFinite(parsed) || parsed <= 0) {
      setError("Enter a valid height.");
      return;
    }

    const valueCm = unit === "CM" ? parsed : parsed * 2.54;
    if (valueCm < 50 || valueCm > 250) {
      setError("Check the height entered (expected 50–250 cm).");
      return;
    }

    setError(null);
    onSubmit(Number(valueCm.toFixed(1)));
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        How tall are you?
      </Text>
      <Text style={styles.subtitle}>
        Optional. Height provides context, though it is not sufficient alone for a size recommendation.
      </Text>

      <TextInput
        style={styles.input}
        value={value}
        onChangeText={setValue}
        keyboardType="decimal-pad"
        placeholder={unit === "CM" ? "170" : "67"}
        accessibilityLabel="Height"
      />

      <View style={styles.unitRow}>
        <Pressable
          onPress={() => setUnit("CM")}
          style={[styles.unitButton, unit === "CM" && styles.unitSelected]}
          accessibilityRole="button"
        >
          <Text style={unit === "CM" ? styles.unitSelectedText : styles.unitText}>CM</Text>
        </Pressable>
        <Pressable
          onPress={() => setUnit("IN")}
          style={[styles.unitButton, unit === "IN" && styles.unitSelected]}
          accessibilityRole="button"
        >
          <Text style={unit === "IN" ? styles.unitSelectedText : styles.unitText}>IN</Text>
        </Pressable>
      </View>

      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : null}

      <Pressable onPress={submit} style={styles.button} accessibilityRole="button">
        <Text style={styles.buttonText}>Continue</Text>
      </Pressable>
      <SkipStepButton onSkip={onSkip} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, gap: 14 },
  title: { fontSize: 24, fontWeight: "700", color: "#111827" },
  subtitle: { fontSize: 13, color: "#4B5563" },
  input: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    backgroundColor: "#fff",
  },
  unitRow: { flexDirection: "row", gap: 12 },
  unitButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
  },
  unitSelected: { backgroundColor: "#111827", borderColor: "#111827" },
  unitText: { color: "#111827", fontWeight: "600" },
  unitSelectedText: { color: "#fff", fontWeight: "600" },
  error: { color: "#B42318", fontSize: 13 },
  button: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontWeight: "600" },
});
