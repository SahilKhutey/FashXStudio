import React from "react";
import { Text, StyleSheet } from "react-native";
import { environment } from "../config/environment";

export function EnvironmentIndicator() {
  if (environment.appEnv === "production") {
    return null;
  }

  return (
    <Text accessibilityLabel="Application environment" style={styles.badge}>
      {environment.appEnv.toUpperCase()}
    </Text>
  );
}

const styles = StyleSheet.create({
  badge: {
    fontSize: 11,
    fontWeight: "600",
    color: "#6B7280",
    letterSpacing: 0.6,
  },
});
