import React, { useState } from "react";
import { View, TextInput, TouchableOpacity, Text, StyleSheet } from "react-native";

interface AIPromptInputProps {
  placeholder?: string;
  onSubmit: (prompt: string) => void;
  disabled?: boolean;
  quickPrompts?: string[];
  testID?: string;
}

export const AIPromptInput: React.FC<AIPromptInputProps> = ({
  placeholder = "Ask anything about fashion, styling, or fit...",
  onSubmit,
  disabled = false,
  quickPrompts = [],
  testID = "ai-prompt-input-component",
}) => {
  const [value, setValue] = useState("");

  const handleSend = () => {
    if (value.trim() && !disabled) {
      onSubmit(value.trim());
      setValue("");
    }
  };

  return (
    <View testID={testID} style={styles.container}>
      {quickPrompts.length > 0 && (
        <View style={styles.quickPromptsRail}>
          {quickPrompts.slice(0, 3).map((prompt, idx) => (
            <TouchableOpacity
              key={idx}
              testID={`quick-prompt-${idx}`}
              style={styles.promptChip}
              onPress={() => onSubmit(prompt)}
            >
              <Text style={styles.promptChipText} numberOfLines={1}>
                {prompt}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={styles.inputRow}>
        <TextInput
          testID="ai-prompt-text-input"
          style={styles.input}
          placeholder={placeholder}
          placeholderTextColor="#8E8E93"
          value={value}
          onChangeText={setValue}
          editable={!disabled}
          multiline
        />
        <TouchableOpacity
          testID="ai-prompt-send-button"
          style={[styles.sendButton, (!value.trim() || disabled) && styles.sendButtonDisabled]}
          onPress={handleSend}
          disabled={!value.trim() || disabled}
          activeOpacity={0.8}
        >
          <Text style={styles.sendButtonText}>↑</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 12,
    backgroundColor: "#FFFFFF",
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  quickPromptsRail: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 10,
  },
  promptChip: {
    backgroundColor: "#F2F2F7",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#E5E5EA",
  },
  promptChipText: {
    fontSize: 12,
    color: "#3A3A3C",
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F2F2F7",
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  input: {
    flex: 1,
    fontSize: 14,
    color: "#1C1C1E",
    minHeight: 36,
    maxHeight: 100,
    paddingVertical: 6,
  },
  sendButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#1C1C1E",
    justifyContent: "center",
    alignItems: "center",
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: "#C7C7CC",
  },
  sendButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
});
