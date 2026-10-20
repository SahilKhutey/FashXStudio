import React from "react";
import { TextInput, TextInputProps, StyleSheet } from "react-native";

export interface InputProps extends TextInputProps {
  hasError?: boolean;
}

export function Input({ hasError, style, ...rest }: InputProps) {
  return (
    <TextInput
      placeholderTextColor="#9CA3AF"
      style={[styles.input, hasError && styles.inputError, style]}
      {...rest}
    />
  );
}

const styles = StyleSheet.create({
  input: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: "#111827",
    backgroundColor: "#FFFFFF",
  },
  inputError: {
    borderColor: "#DC2626",
    backgroundColor: "#FEF2F2",
  },
});
