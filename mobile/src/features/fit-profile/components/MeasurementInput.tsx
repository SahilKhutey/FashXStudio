import React, { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import type { MeasurementUnit } from "../types";

type InputUnit = "CM" | "IN" | "MM" | "KG";

interface Props {
  title: string;
  explanation: string;
  fieldCode?: string;
  initialValue?: string;
  initialUnit?: InputUnit;
  allowedUnits?: InputUnit[];
  hasExistingValue?: boolean;
  onSave: (
    value: string,
    unit: MeasurementUnit,
    confirmUnusual?: boolean,
  ) => Promise<void>;
  onDelete?: () => Promise<void>;
}

function previewNormalized(rawValue: string, unit: InputUnit): string | null {
  const parsed = Number(rawValue.trim());
  if (!Number.isFinite(parsed) || parsed <= 0) return null;
  if (unit === "KG") return `${parsed.toFixed(2)} KG`;
  if (unit === "IN") return `${(parsed * 2.54).toFixed(2)} CM`;
  if (unit === "MM") return `${(parsed / 10).toFixed(2)} CM`;
  return `${parsed.toFixed(2)} CM`;
}

export function MeasurementInput({
  title,
  explanation,
  fieldCode,
  initialValue = "",
  initialUnit,
  allowedUnits,
  hasExistingValue = false,
  onSave,
  onDelete,
}: Props) {
  const units: InputUnit[] =
    allowedUnits ??
    (fieldCode?.toUpperCase() === "WEIGHT" ? ["KG"] : ["CM", "IN", "MM"]);

  const [value, setValue] = useState(initialValue);
  const [unit, setUnit] = useState<InputUnit>(initialUnit ?? units[0] ?? "CM");
  const [confirmReplace, setConfirmReplace] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const normalizedPreview = previewNormalized(value, unit);

  async function submit(confirmUnusual = false) {
    const trimmed = value.trim();
    const parsed = Number(trimmed);

    if (!trimmed || !Number.isFinite(parsed) || parsed <= 0) {
      setError("Enter a valid positive measurement.");
      return;
    }

    if (!/^\d+(\.\d{1,3})?$/.test(trimmed)) {
      setError("Use up to three decimal places.");
      return;
    }

    if (hasExistingValue && !confirmReplace) {
      setConfirmReplace(true);
      return;
    }

    setError(null);
    setSaving(true);

    try {
      await onSave(trimmed, unit, confirmUnusual);
      setConfirmReplace(false);
    } catch {
      setError("Could not save this measurement. Check the value and try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.explanation}>{explanation}</Text>

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={(text) => {
            setValue(text);
            setConfirmReplace(false);
          }}
          keyboardType="decimal-pad"
          placeholder="Enter measurement"
          accessibilityLabel={`${title} measurement`}
        />
        <Text style={styles.unitTag}>{unit}</Text>
      </View>

      {normalizedPreview ? (
        <Text style={styles.preview}>Normalized preview: {normalizedPreview}</Text>
      ) : null}

      <View style={styles.unitRow} accessibilityRole="radiogroup">
        {units.map((item) => {
          const selected = unit === item;
          return (
            <Pressable
              key={item}
              style={[styles.unitPill, selected && styles.selectedUnitPill]}
              onPress={() => setUnit(item)}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              accessibilityLabel={`Unit ${item}`}
            >
              <Text
                style={[
                  styles.unitPillText,
                  selected && styles.selectedUnitPillText,
                ]}
              >
                {item}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {confirmReplace ? (
        <Text style={styles.confirmPrompt} accessibilityRole="alert">
          Press Save again to confirm replacing your saved {title.toLowerCase()} measurement.
        </Text>
      ) : null}

      {error ? (
        <Text style={styles.errorText} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}

      <View style={styles.actionsRow}>
        <Pressable
          style={[styles.saveButton, saving && styles.disabledButton]}
          onPress={() => submit(false)}
          disabled={saving}
          accessibilityRole="button"
        >
          <Text style={styles.saveButtonText}>
            {saving
              ? "Saving..."
              : confirmReplace
                ? "Confirm update"
                : "Save measurement"}
          </Text>
        </Pressable>

        {onDelete ? (
          <Pressable
            style={styles.deleteButton}
            onPress={onDelete}
            disabled={saving}
            accessibilityRole="button"
          >
            <Text style={styles.deleteButtonText}>Remove</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    marginVertical: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 4,
  },
  explanation: {
    fontSize: 13,
    color: "#4B5563",
    marginBottom: 10,
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    color: "#111827",
  },
  unitTag: {
    fontSize: 13,
    fontWeight: "700",
    color: "#0F766E",
    minWidth: 28,
  },
  preview: {
    fontSize: 12,
    color: "#6B7280",
    marginTop: 6,
  },
  unitRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 10,
  },
  unitPill: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    backgroundColor: "#F9FAFB",
  },
  selectedUnitPill: {
    borderColor: "#0F766E",
    backgroundColor: "#F0FDFA",
  },
  unitPillText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#4B5563",
  },
  selectedUnitPillText: {
    color: "#0F766E",
  },
  confirmPrompt: {
    marginTop: 8,
    fontSize: 12,
    color: "#B45309",
  },
  errorText: {
    marginTop: 8,
    fontSize: 12,
    color: "#DC2626",
  },
  actionsRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 12,
  },
  saveButton: {
    flex: 1,
    backgroundColor: "#0F766E",
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
  },
  disabledButton: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
  deleteButton: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#FCA5A5",
    alignItems: "center",
  },
  deleteButtonText: {
    color: "#B91C1C",
    fontSize: 13,
    fontWeight: "600",
  },
});
