import React, { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useCreateSavedLook } from "../hooks";

interface Props {
  selectedItemIds: string[];
  onCreated: (lookId: string) => void;
}

export function CreateLookForm({ selectedItemIds, onCreated }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const createMutation = useCreateSavedLook();

  const dedupedIds = Array.from(new Set(selectedItemIds));
  const canSubmit =
    title.trim().length > 0 &&
    dedupedIds.length > 0 &&
    !createMutation.isPending;

  async function submit() {
    if (!canSubmit) return;
    const result = await createMutation.mutateAsync({
      title: title.trim(),
      description: description.trim() || undefined,
      item_ids: dedupedIds,
    });
    onCreated(result.id);
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        Create a look
      </Text>

      <TextInput
        style={styles.input}
        value={title}
        onChangeText={setTitle}
        placeholder="Look name"
        maxLength={100}
        accessibilityLabel="Look name"
      />

      <TextInput
        style={styles.input}
        value={description}
        onChangeText={setDescription}
        placeholder="Description (optional)"
        maxLength={1000}
        multiline
        accessibilityLabel="Look description"
      />

      <Text style={styles.count}>{dedupedIds.length} items selected</Text>

      <Pressable
        disabled={!canSubmit}
        onPress={() => {
          void submit();
        }}
        accessibilityRole="button"
        style={[styles.button, !canSubmit && styles.disabled]}
      >
        <Text style={styles.buttonText}>
          {createMutation.isPending ? "Saving..." : "Save look"}
        </Text>
      </Pressable>

      {createMutation.isError ? (
        <Text accessibilityRole="alert" style={styles.error}>
          Unable to save your look. Please retry.
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, gap: 14 },
  title: { fontSize: 22, fontWeight: "700", color: "#111827" },
  input: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    backgroundColor: "#FFFFFF",
  },
  count: { fontSize: 13, color: "#4B5563" },
  button: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  disabled: { backgroundColor: "#9CA3AF" },
  buttonText: { color: "#FFFFFF", fontWeight: "600" },
  error: { color: "#B42318", fontSize: 13 },
});
