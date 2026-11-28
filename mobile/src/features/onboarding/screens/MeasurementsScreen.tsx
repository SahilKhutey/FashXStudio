import React, { useState } from "react";
import { View, Text, TextInput, Pressable, ScrollView, StyleSheet } from "react-native";
import type { MeasurementKey } from "../onboarding.types";
import { SkipStepButton } from "../components/SkipStepButton";

const FIELDS: { key: MeasurementKey; label: string }[] = [
  { key: "CHEST", label: "Chest" },
  { key: "WAIST", label: "Waist" },
  { key: "HIP", label: "Hip" },
  { key: "SHOULDER", label: "Shoulder" },
  { key: "INSEAM", label: "Inseam" },
  { key: "SLEEVE_LENGTH", label: "Sleeve length" },
];

type Props = {
  onContinue: (values: Partial<Record<MeasurementKey, number>>) => void;
  onSkip: () => void;
};

export function MeasurementsScreen({ onContinue, onSkip }: Props) {
  const [values, setValues] = useState<Partial<Record<MeasurementKey, string>>>({});
  const [error, setError] = useState<string | null>(null);

  function submit() {
    const result: Partial<Record<MeasurementKey, number>> = {};
    for (const field of FIELDS) {
      const raw = values[field.key];
      if (!raw?.trim()) continue;
      const parsed = Number(raw);
      if (!Number.isFinite(parsed) || parsed <= 0 || parsed > 300) {
        setError(`Check the ${field.label} measurement.`);
        return;
      }
      result[field.key] = Number(parsed.toFixed(1));
    }
    setError(null);
    onContinue(result);
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Optional body measurements
      </Text>
      <Text style={styles.subtitle}>
        Enter any body measurements (not garment measurements) you know to compare with verified merchant size charts. You can skip any or all fields.
      </Text>

      {FIELDS.map((field) => (
        <View key={field.key} style={styles.field}>
          <Text style={styles.label}>{field.label} (cm)</Text>
          <TextInput
            style={styles.input}
            value={values[field.key] ?? ""}
            onChangeText={(value) =>
              setValues((current) => ({ ...current, [field.key]: value }))
            }
            keyboardType="decimal-pad"
            placeholder="Optional"
            accessibilityLabel={`${field.label} in cm`}
          />
        </View>
      ))}

      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : null}

      <Pressable onPress={submit} style={styles.button} accessibilityRole="button">
        <Text style={styles.buttonText}>Continue</Text>
      </Pressable>
      <SkipStepButton onSkip={onSkip} label="Skip measurements" />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 12 },
  title: { fontSize: 24, fontWeight: "700", color: "#111827" },
  subtitle: { fontSize: 13, color: "#4B5563" },
  field: { gap: 4 },
  label: { fontSize: 13, fontWeight: "600", color: "#374151" },
  input: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 10,
    padding: 10,
    fontSize: 15,
    backgroundColor: "#fff",
  },
  error: { color: "#B42318", fontSize: 13 },
  button: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 4,
  },
  buttonText: { color: "#fff", fontWeight: "600" },
});
